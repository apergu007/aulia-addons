# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler'),
        ], string='PR Type')

    quality_teams_id = fields.Many2one('quality.alert.team', 'Quality Teams')