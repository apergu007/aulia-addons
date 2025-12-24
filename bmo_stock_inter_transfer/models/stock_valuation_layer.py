from odoo import _, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

from itertools import chain
from odoo.tools import groupby, OrderedSet
from collections import defaultdict


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    def _validate_accounting_entries(self):
        am_vals = []
        aml_to_reconcile = defaultdict(set)
        move_ids = OrderedSet()
        svl_move_list = defaultdict(int) 
        for svl in self:
            if not svl.with_company(svl.company_id).product_id.valuation == 'real_time':
                continue

            move = svl.stock_move_id
            if not move:
                move = svl.stock_valuation_layer_id.stock_move_id

            if not move._is_internal_transfer():
                continue
            move_ids.add(move.id)
            svl_move_list[svl.id] = move.id

        moves = self.env['stock.move'].browse(move_ids)
        move_directions = moves._get_move_directions()
        for svl in self:
            linked_move = moves.browse(svl_move_list[svl.id])
            if linked_move:
                am_vals += linked_move.with_context(move_directions=move_directions).with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)

        if am_vals:
            account_moves = self.env['account.move'].sudo().create(am_vals)
            account_moves._post()

            # update stock valuation layer
            for move in account_moves.mapped('stock_move_id'):
                svls = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)])
                svls.write({'account_move_id': account_moves.filtered(lambda am: am.stock_move_id == move).id})
            
        return super()._validate_accounting_entries()