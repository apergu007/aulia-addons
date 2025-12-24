from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    @api.depends('default_code','name')
    def _compute_display_name(self):
        for template in self:
            item_code = self.env.user.has_group('bmo_mrp.see_item_code')
            item_name = self.env.user.has_group('bmo_mrp.see_product_name')
            name = 'Belum Di set Config'
            if item_code:
                name = template.default_code
            elif item_name:
                name = template.name
            if item_code and item_name:
                name = f'[{template.default_code}] {template.name}'
            template.display_name = name

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    @api.depends('default_code','name')
    def _compute_display_name(self):
        for pp in self:
            item_code = self.env.user.has_group('bmo_mrp.see_item_code')
            item_name = self.env.user.has_group('bmo_mrp.see_product_name')
            name = 'Belum Di set Config'
            if item_code:
                name = pp.default_code
            elif item_name:
                name = pp.name
            if item_code and item_name:
                name = f'[{pp.default_code}] {pp.name}'
            pp.display_name = name
    
    # @api.depends('default_code','name')
    # def _compute_display_name(self):
    #     for pp in self:
    #         template = pp.product_tmpl_id
    #         name = template.default_code
    #         if self.env.user.has_group('bmo_mrp.see_product_name_code'):
    #             name = '[%s] %s' % (template.default_code, template.name)
    #         pp.display_name = name