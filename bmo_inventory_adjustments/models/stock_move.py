# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare, float_is_zero, OrderedSet

import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = "stock.move"

    x_inventory_id = fields.Many2one('stock.inventory', 'Inventory Adjusment')
    x_inventory_line_id = fields.Many2one('stock.inventory.line', 'Inventory Line Adjusment')

