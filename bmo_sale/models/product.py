from odoo import fields, models, api, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    sale_categ_id = fields.Many2one('sales.category', 'Sales Category')

class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one('master.brand', 'Brand')

class ProductProdct(models.Model):
    _inherit = "product.product"

    brand_id = fields.Many2one('master.brand', related="product_tmpl_id.brand_id", store=True)