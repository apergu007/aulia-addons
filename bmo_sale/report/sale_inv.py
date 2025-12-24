# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from odoo.tools import formatLang

class SaleInvUnion(models.Model):
    _name = 'sale.inv.union'
    _auto = False
    _description = 'Sale & Inv Union'
    _order = "date desc, name desc"
    _rec_names_search = ['name', 'reference']

    name = fields.Char(string='Reference', readonly=True)
    reference = fields.Char(string='Source', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    customer_inv_id = fields.Many2one('account.move', string='Invoice Bill', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    is_show = fields.Boolean(string='Show', readonly=True)
    

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sale_inv_union')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW sale_inv_union AS (
                SELECT
                    id,
                    name,
                    ref as reference,
                    partner_id,
                    date,
                    amount_untaxed as amount,
                    currency_id,
                    company_id,
                    id as customer_inv_id,
                    NULL as sale_order_id,
                    FALSE as is_show
                FROM account_move
                WHERE move_type = 'out_invoice' AND state = 'posted'

            UNION

                SELECT
                    -s.id,
                    s.name,
                    s.client_order_ref as reference,
                    s.partner_id,
                    s.date_order::date as date,
                    s.amount_untaxed as amount,
                    s.currency_id,
                    s.company_id,
                    NULL as customer_inv_id,
                    s.id as sale_order_id,
                    CASE WHEN s.invoice_status = 'no' THEN FALSE ELSE TRUE END as is_show
                FROM sale_order s
                WHERE s.state IN ('sale', 'done') AND s.invoice_status IN ('to invoice', 'no')
            )""")

    @api.depends('currency_id', 'reference', 'amount', 'sale_order_id')
    @api.depends_context('show_total_amount')
    def _compute_display_name(self):
        for doc in self:
            name = doc.name or ''
            if doc.reference:
                name += ' - ' + doc.reference
            amount = doc.amount
            if doc.sale_order_id and doc.sale_order_id.invoice_status == 'no':
                amount = 0.0
            name += ': ' + formatLang(self.env, amount, currency_obj=doc.currency_id)
            doc.display_name = name
