from odoo import api, fields, models, tools
from odoo.tools import float_compare, float_is_zero
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger(__name__)

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    categ_id = fields.Many2one(related='product_id.categ_id', store=True)
    x_inventory_id = fields.Many2one('stock.inventory', 'Inventory Adjusment')