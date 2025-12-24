# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import deque

from odoo import api, Command, fields, models, _
from odoo.tools.float_utils import float_round, float_is_zero, float_compare
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    po_line_id = fields.Many2one(
        'purchase.order.line', 'PO Line', copy=True)