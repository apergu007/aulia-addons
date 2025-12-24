from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_repr, float_round, float_compare
from odoo.exceptions import ValidationError
from collections import defaultdict
from datetime import datetime

class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_discount_account_id = fields.Many2one(
        'account.account', 'Discount Account', company_dependent=True, ondelete='restrict', domain="[('deprecated', '=', False)]", check_company=True)