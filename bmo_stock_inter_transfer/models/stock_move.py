# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, float_compare, OrderedSet

import logging
_logger = logging.getLogger(__name__)

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    enable_custom_internal_trans = fields.Boolean(string="Use Custom Internal Transfer Accounting")


class StockMove(models.Model):
    _inherit = 'stock.move'

    internal_value_unit = fields.Float(string="Internal Transfer Unit Value", digits='Product Price')

    def _is_internal_transfer(self):
        self.ensure_one()
        return (self.location_id.usage == 'internal' and self.location_dest_id.usage == 'internal' and self.picking_type_id.enable_custom_internal_trans)

    # Ambil akun sumber
    def _get_src_account(self, accounts_data):
        if self._is_internal_transfer():
            return (self.company_id.inter_locations_clearing_account_id.id or accounts_data['inter_locations_clearing'].id or accounts_data['stock_input'].id)
        return super()._get_src_account(accounts_data)

    # Ambil akun tujuan
    def _get_dest_account(self, accounts_data):
        if self._is_internal_transfer():
            return self.company_id.inter_locations_clearing_account_id.id or accounts_data['inter_locations_clearing'].id or accounts_data['stock_input'].id
        return super()._get_dest_account(accounts_data)
    
    @api.model
    def _get_valued_types(self):
        return super()._get_valued_types() + ['internal_transfer']
    
    def _get_move_directions(self):
        move_directions = super()._get_move_directions()

        for record in self:
            if record._is_internal_transfer():
                move_directions[record.id].add('internal_transfer')

        return move_directions

    def _create_internal_transfer_svl(self, quantity=None):
        """Create ZERO-value SVL for internal transfers (multi-record safe)."""
        SVL = self.env['stock.valuation.layer']
        created_svls = SVL.browse()

        for move in self:
            if not move._is_internal_transfer():
                continue
            # Ambil unit cost dari lot jika ada, else dari product
            unit_cost = move.product_id.standard_price
            if move.lot_ids:
                first_lot = move.lot_ids[:1]
                if first_lot.standard_price:
                    unit_cost = first_lot.standard_price
            svl_vals = {
                'product_id': move.product_id.id,
                'company_id': move.company_id.id,
                'stock_move_id': move.id,
                'description': "%s %s (Internal Transfer No-Value No-Qty)" % (move.picking_id.name, move.product_id.display_name),
                'quantity': 0,
                'unit_cost': unit_cost,
                'value': 0.0,
                'remaining_value': 0.0,
                'remaining_qty': 0,
            }

            # create recordset dan gabungkan dengan previous
            created_svls |= SVL.sudo().create(svl_vals)

        return created_svls

    def _create_internal_transfer_journal(self, return_move=False):
        """Create journal entry for internal transfer move (multi-record safe)."""
        self.ensure_one()
        am_vals = []

        accounts_data = self.product_id.product_tmpl_id._get_product_accounts()

        # Ambil journal (prioritas: picking type → product → company / location fallback)
        journal =  getattr(accounts_data.get('inter_locatistock_journalons_clearing'), 'id', False) or self.product_id.categ_id.property_stock_journal.id

        if not journal:
            raise UserError(_("Please configure journal for internal transfer."))

        # Source / Dest Account
        acc_src = getattr(accounts_data.get('inter_locations_clearing'), 'id', False)
        acc_dest = getattr(accounts_data.get('stock_valuation'), 'id', False)

        if not acc_src or not acc_dest:
            raise UserError(_("Account Belum di Setup"))

        # Hitung value: pakai internal_value_unit jika ada, else price_unit
        move_cost = self._get_price_unit()
        price_unit = next(iter(move_cost.values()))
        self.internal_value_unit = price_unit
        self.price_unit = price_unit
        value = self.product_uom_qty * price_unit
        if value <= 0:
            return False  # skip jika 0

        # Tentukan debit/credit sesuai return atau normal
        if return_move:
            # Return: debit source, credit dest
            move_lines = [
                (0, 0, {
                    'name': self.name,
                    'debit': value,
                    'credit': 0.0,
                    'account_id': acc_src,
                }),
                (0, 0, {
                    'name': self.name,
                    'debit': 0.0,
                    'credit': value,
                    'account_id': acc_dest,
                }),
            ]
        else:
            # Normal: debit dest, credit source
            move_lines = [
                (0, 0, {
                    'name': self.name,
                    'debit': value,
                    'credit': 0.0,
                    'account_id': acc_dest,
                }),
                (0, 0, {
                    'name': self.name,
                    'debit': 0.0,
                    'credit': value,
                    'account_id': acc_src,
                }),
            ]

        am_vals.append({
            'journal_id': journal,
            'line_ids': move_lines,
            'date': fields.Date.context_today(self),
            'ref': self.picking_id.name,
            'move_type': 'entry',
            'stock_move_id': self.id,
            'company_id': self.company_id.id,
        })

        return am_vals


    def _account_entry_move(self, qty, description, svl_id, cost):
        if self._is_internal_transfer():
            if not self.origin_returned_move_id:
                account_move_id = self._create_internal_transfer_journal(return_move=True)
            else:
                account_move_id = self._create_internal_transfer_journal(return_move=False)

            return account_move_id
        return super()._account_entry_move(qty, description, svl_id, cost)


    def _prepare_anglosaxon_account_move_vals(self, acc_src, acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost):
        accounts_data = self.product_id.product_tmpl_id._get_product_accounts()

        if self._is_production_consumed():
            inter_loc_acc = getattr(accounts_data.get('inter_locations_clearing'), 'id', False)
            production_acc = getattr(accounts_data.get('production'), 'id', False)
            # Jika tidak ada transit account → pakai default Odoo
            if not inter_loc_acc:
                return super()._prepare_anglosaxon_account_move_vals(acc_src, acc_dest, acc_valuation, journal_id, qty,description, svl_id, cost)

            # Konsumsi normal
            if not self.origin_returned_move_id:
                acc_src = inter_loc_acc
                acc_dest = production_acc
            else:
                # Konsumsi retur
                acc_src = production_acc
                acc_dest = inter_loc_acc

        # Kirim ke Odoo untuk proses jurnal final
        return super()._prepare_anglosaxon_account_move_vals(acc_src, acc_dest, acc_valuation, journal_id, qty,description, svl_id, cost)

