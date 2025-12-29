# -*- coding: utf-8 -*-

import pytz
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare, float_is_zero

import logging
_logger = logging.getLogger(__name__)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_inventory_id = fields.Many2one('stock.inventory', 'Inventory Adjusment')
    