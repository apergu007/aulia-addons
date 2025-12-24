from collections import defaultdict
from contextlib import contextmanager, ExitStack
from datetime import date
import logging
import re

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import frozendict, format_date, float_compare, format_list, Query
from odoo.tools.sql import create_index, SQL
from odoo.addons.web.controllers.utils import clean_action

from odoo.addons.account.models.account_move import MAX_HASH_VERSION


_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    @api.depends('account_id', 'company_id', 'discount', 'price_unit', 'quantity', 'currency_rate')
    def _compute_discount_allocation_needed(self):
        for line in self:
            line.discount_allocation_dirty = True
            discount_allocation_account = line.move_id._get_discount_allocation_account()
            if line.product_id and line.product_id.categ_id.property_discount_account_id:
                discount_allocation_account = line.product_id.categ_id.property_discount_account_id

            if not discount_allocation_account or line.display_type != 'product' or line.currency_id.is_zero(line.discount):
                line.discount_allocation_needed = False
                continue

            discounted_amount_currency = line.currency_id.round(line.move_id.direction_sign * line.quantity * line.price_unit * line.discount/100)
            discount_allocation_needed = {}
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    'account_id': line.account_id.id,
                    'move_id': line.move_id.id,
                    'currency_rate': line.currency_rate,
                }),
                {
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': 0.0,
                },
            )
            discount_allocation_needed_vals['amount_currency'] += discounted_amount_currency
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    'move_id': line.move_id.id,
                    'account_id': discount_allocation_account.id,
                    'currency_rate': line.currency_rate,
                }),
                {
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': 0.0,
                },
            )
            discount_allocation_needed_vals['amount_currency'] -= discounted_amount_currency
            line.discount_allocation_needed = {k: frozendict(v) for k, v in discount_allocation_needed.items()}