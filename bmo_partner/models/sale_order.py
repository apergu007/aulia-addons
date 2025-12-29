from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one('res.partner',domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_customer', '=', True)]",)
    # partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', domain=[('is_customer', '=', True)])
    # partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', domain=[('is_customer', '=', True)])

    @api.onchange('partner_id')
    def _onchange_wh_partner_id(self):
        for so in self:
            if so.partner_id and so.partner_id.warehouse_id:
                so.warehouse_id = so.partner_id.warehouse_id.id