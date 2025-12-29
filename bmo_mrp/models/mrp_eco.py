from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MrpEco(models.Model):
    _inherit = 'mrp.eco'

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id.bom_ids:
            bom_product_tmpl = self.bom_id.product_tmpl_id or self.bom_id.product_id.product_tmpl_id
            if bom_product_tmpl != self.product_tmpl_id:
                list_boms = self.product_tmpl_id.bom_ids.filtered(lambda bm: bm.show_plm == True)
                boms = False
                if list_boms:
                    boms = list_boms.ids[0]
                self.bom_id = boms