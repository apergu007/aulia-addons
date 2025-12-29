from odoo import _, api, fields, models
from odoo.exceptions import UserError

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"
