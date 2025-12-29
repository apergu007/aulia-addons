from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    code_partner = fields.Char('Code Partner')
    is_customer = fields.Boolean(string="Is Customer")
    is_vendor = fields.Boolean(string="Is Vendor")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    ship_to = fields.Text('Ship To')

    @api.depends("code_partner", "name")
    def _compute_display_name(self):
        for doc in self:
            name = f'[{doc.code_partner}] {doc.name}' if doc.code_partner else doc.name
            doc.display_name = name