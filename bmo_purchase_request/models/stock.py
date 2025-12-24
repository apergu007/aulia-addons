from collections import defaultdict

from odoo import api, fields, models, _
from odoo.osv.expression import AND


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    pr_line_ids = fields.One2many('purchase.request.line', 'group_id', string='Linked Purchase Request Lines', copy=False)
    