from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    manual_cost_price = fields.Float('Manual Cost')