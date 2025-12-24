# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def _get_product_accounts(self):
        accounts = super()._get_product_accounts()
        accounts.update({'inter_locations_clearing': self.categ_id.property_inter_locations_clearing_account_id,})
        return accounts

class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_inter_locations_clearing_account_id = fields.Many2one(
        'account.account', 'Inter-locations Clearing Account', company_dependent=True, ondelete='restrict')

    def _get_stock_account_property_field_names(self):
        return super()._get_stock_account_property_field_names() + ['property_inter_locations_clearing_account_id']
