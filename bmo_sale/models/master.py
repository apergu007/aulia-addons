from odoo import fields, models, api, _


class MasterBrand(models.Model):
    _name = "master.brand"
    _description = "Master Brand"

    name = fields.Char('Name')

class SalesCategory(models.Model):
    _name = "sales.category"
    _description = "Sales Category"

    name = fields.Char('Name')