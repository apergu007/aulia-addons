import difflib
import time
from markupsafe import Markup
from odoo import api, fields, models, Command, _

import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_customer_inv_id = fields.Many2one('sale.inv.union', store=False, readonly=False,
        string='Auto-complete from Sale & Inv',
        help="Auto-complete from a past Inv / Sale order.")
    sale_order_id = fields.Many2one('sale.order', store=False, readonly=False,
        string='Sale Order',
        help="Auto-complete from a past Sale order.")
    
    # === Customer Invoice fields === #
    invoice_customer_inv_id = fields.Many2one(
        'account.move',
        store=False,
        check_company=True,
        string='Customer Invoice',
    )


    def _add_sale_order_lines(self, sale_order_lines):
        """ Creates new invoice lines from Sale order lines """
        self.ensure_one()
        new_line_ids = self.env['account.move.line']

        for so_line in sale_order_lines:
            new_line_values = so_line._prepare_account_move_line(self)
            print(new_line_values,'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            new_line_ids += self.env['account.move.line'].new(new_line_values)

        self.invoice_line_ids += new_line_ids

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    # @api.onchange('invoice_customer_inv_id')
    # def _onchange_invoice_customer_inv(self):
    #     if self.invoice_customer_inv_id:
    #         # Copy invoice lines.
    #         for line in self.invoice_customer_inv_id.invoice_line_ids:
    #             copied_vals = line.copy_data()[0]
    #             self.invoice_line_ids += self.env['account.move.line'].new(copied_vals)

    #         self.currency_id = self.invoice_customer_inv_id.currency_id
    #         self.fiscal_position_id = self.invoice_customer_inv_id.fiscal_position_id

    #         # Reset
    #         self.invoice_customer_inv_id = False

    @api.onchange('sale_customer_inv_id', 'sale_order_id')
    def _onchange_sale_auto_complete(self):
        if self.sale_customer_inv_id.customer_inv_id:
            self.invoice_customer_inv_id = self.sale_customer_inv_id.customer_inv_id
            self._onchange_invoice_customer_inv()
        elif self.sale_customer_inv_id.sale_order_id:
            self.sale_order_id = self.sale_customer_inv_id.sale_order_id
        self.sale_customer_inv_id = False

        if not self.sale_order_id:
            return

        # Copy data from SO
        invoice_vals = self.sale_order_id.with_company(self.sale_order_id.company_id)._prepare_invoice()
        has_invoice_lines = bool(self.invoice_line_ids.filtered(lambda x: x.display_type not in ('line_note', 'line_section')))
        new_currency_id = self.currency_id if has_invoice_lines else invoice_vals.get('currency_id')
        del invoice_vals['ref'], invoice_vals['payment_reference']
        del invoice_vals['company_id']  # avoid recomputing the currency
        if self.move_type == invoice_vals['move_type']:
            del invoice_vals['move_type'] # no need to be updated if it's same value, to avoid recomputes
        self.update(invoice_vals)
        self.currency_id = new_currency_id

        # Copy Sale lines.
        so_lines = self.sale_order_id.order_line - self.invoice_line_ids.mapped('sale_line_ids')
        print(so_lines,'VVVVVVVVVVVVVVVVVVVVVVVV')
        self._add_sale_order_lines(so_lines)

        # Compute invoice_origin.
        # origins = set(self.invoice_line_ids.mapped('sale_line_ids.order_id.name'))
        # self.invoice_origin = ','.join(list(origins))
        for line in self.line_ids:
            print(line.sale_line_ids, 'WWWWWWWWWWWWWWWWWWWWWWWWWWWWW',line.name)
        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ', '.join(refs)

        # Compute payment_reference.
        if not self.payment_reference:
            if len(refs) == 1:
                self.payment_reference = refs[0]
            elif len(refs) > 1:
                self.payment_reference = refs[-1]

        # Copy company_id (only changes if the id is of a child company (branch))
        if self.company_id != self.sale_order_id.company_id:
            self.company_id = self.sale_order_id.company_id

        self.sale_order_id = False