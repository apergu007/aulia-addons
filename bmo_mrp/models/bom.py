from odoo import fields, models, api, _
from odoo.osv.expression import AND, OR


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_no = fields.Char('BOM No.', tracking=True)
    decription = fields.Char('Description', tracking=True)
    min_qty = fields.Float('Minimum Quantity', tracking=True)
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    total_cost_pcs = fields.Float('Total Cost/Pcs', compute='_compute_total_cost', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),('post', 'Posted'),
        ], string='Status', default='draft', tracking=True)
    tipe_produksi = fields.Selection([
        ('Mixing', 'Mixing'), ('Filling', 'Filling'), ('Packing', 'Packing')
    ], string="Tipe Produksi", tracking=True)
    show_plm = fields.Boolean(string='Muncul PLM ?', tracking=True)

    @api.depends('bom_line_ids','bom_line_ids.total_cost')
    def _compute_total_cost(self):
        for l in self:
            res = res_pcs = 0
            if l.bom_line_ids:
                res = sum(l.bom_line_ids.mapped('total_cost'))
                res_pcs = 0 if res == 0 else res / l.product_qty
            l.total_cost = res
            l.total_cost_pcs = res_pcs

    def action_post(self):
        return self.write({'state': 'post', 'show_plm': False})
    
    def action_draft(self):
        return self.write({'state': 'draft', 'show_plm': True})
        

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    manual_cost_price = fields.Float('Standard Cost')
    total_manual_cost_price = fields.Float('Total Standard Cost', compute='_compute_total_cost', store=True)
    standard_cost = fields.Float('Cost')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    item_desc = fields.Char('Item Description')
    

    @api.onchange('product_id')
    def onchange_product_id(self):
        for l in self:
            if l.product_id:
                l.item_desc = l.product_id.name
                l.product_uom_id = l.product_id.uom_id.id
                l.manual_cost_price = l.product_id.product_tmpl_id.manual_cost_price
                l.standard_cost = l.product_id.product_tmpl_id.standard_price
    
    @api.depends('product_qty','manual_cost_price','standard_cost')
    def _compute_total_cost(self):
        for l in self:
            l.total_manual_cost_price = l.product_qty * l.manual_cost_price
            l.total_cost = l.product_qty * l.standard_cost