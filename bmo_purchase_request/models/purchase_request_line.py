from odoo import _, api, fields, models
from odoo.exceptions import UserError

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    group_id = fields.Many2one('procurement.group', string="Procurement Group",)
    unit_price = fields.Float(
        string="Unit Price", required=True, default=0.0,
        help="Unit price of the product in the purchase request line. This is the price that will be used to calculate the total cost of the purchase request line.")
    estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True)
    
    @api.depends('unit_price','product_qty')
    def _compute_estimated_cost(self):
        for line in self:
            line.estimated_cost = line.unit_price * line.product_qty