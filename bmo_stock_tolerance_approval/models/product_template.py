# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tolerance_type = fields.Selection(
        [('percent', 'Percent'), ('fixed', 'Fixed Quantity')],
        string='Tolerance Type',
        default='percent',
        help='Type of tolerance to apply when receiving: percent or fixed quantity.'
    )

    tolerance_value = fields.Float(
        string='Tolerance Value',
        help='If Percent: value in percent (e.g. 5 for 5%).\nIf Fixed: value in product UoM units.'
    )