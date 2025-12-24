from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date 
from collections import defaultdict

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    tipe_produksi = fields.Selection([
        ('Mixing', 'Mixing'), ('Filling', 'Filling'), ('Packing', 'Packing')
    ], string="Tipe Produksi", related="bom_id.tipe_produksi")
    mrp_type = fields.Selection([
        ('reguler', 'Reqular'),('maklon', 'Maklon'),
        ('sample', 'Sample')], string='MRP Type')
    ok_date = fields.Date('OK Date')
    qty_min_bom = fields.Float('Qty Min Bom', related='bom_id.min_qty')
    is_qty_bom = fields.Boolean('Qty Sesuai Bom', compute="_compute_is_qty_bom", store=True)
    is_qty_ok = fields.Boolean('Qty Min Bom', copy=False)

    @api.depends('qty_producing', 'bom_id.min_qty')
    def _compute_is_qty_bom(self):
        for b in self:
            qty = True
            qty_oke = True
            if b.qty_producing < b.bom_id.min_qty:
                qty = False
                qty_oke = False
            b.is_qty_bom = qty
            b.is_qty_ok = qty_oke

    def button_mark_done(self):
        self.ensure_one()
        if not self.is_qty_ok:
            return {
                'name': "Apakah Anda Yakin memproduksi dibawah Qty Bom?",
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'wizard.confirmation',
                'view_id': self.env.ref('bmo_mrp.wizard_confirmation_form').id,
                'target': 'new',
            }
        return super(MrpProduction, self).button_mark_done()

    @api.depends('product_id', 'never_product_template_attribute_value_ids')
    def _compute_bom_id(self):
        mo_by_company_id = defaultdict(lambda: self.env['mrp.production'])
        for mo in self:
            if not mo.product_id and not mo.bom_id:
                mo.bom_id = False
                continue
            mo_by_company_id[mo.company_id.id] |= mo

        for company_id, productions in mo_by_company_id.items():
            picking_type_id = self._context.get('default_picking_type_id')
            picking_type = picking_type_id and self.env['stock.picking.type'].browse(picking_type_id)
            boms_by_product = self.env['mrp.bom'].with_context(active_test=True)._bom_find(productions.product_id, picking_type=picking_type, company_id=company_id, bom_type='normal')
            for production in productions:
                if not production.bom_id or production.bom_id.product_tmpl_id != production.product_tmpl_id or (production.bom_id.product_id and production.bom_id.product_id != production.product_id):
                    bom = boms_by_product[production.product_id].filtered(lambda l: l.state == 'post')
                    production.bom_id = bom.id or False
                    self.env.add_to_compute(production._fields['picking_type_id'], production)
    
    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        res = super(MrpProduction, self)._get_move_raw_values(product, product_uom_qty, product_uom, operation_id=False, bom_line=False)
        scrap_src = self.env['stock.scrap'].search([('production_id','=', self.id)])
        if scrap_src:
            scrap_qty = 0 if not scrap_src else round(sum(scrap_src.mapped('scrap_qty')), 2)
            res['product_uom_qty'] = product_uom_qty - scrap_qty
        return res
    
    # def action_confirm(self):
    #     if not self.bom_id:
    #         raise ValidationError(_("Bom Tidak Boleh Kosong."))
    #     return super(MrpProduction, self).action_confirm()
    
    # def _get_moves_raw_values(self):
    #     moves = []
    #     for production in self:
    #         if not production.bom_id:
    #             continue
    #         factor = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
    #         print(production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id),'ddddddddd',production.bom_id.product_qty)
    #         # _boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id, 
    #         # never_attribute_values=production.never_product_template_attribute_value_ids)
    #         # factor = self.product_qty / production.bom_id.product_qty
    #         lines = production.bom_id.bom_line_ids
    #         for bom_line in lines:
    #             if bom_line.bom_id.id == self.bom_id.id:
    #                 operation = bom_line.operation_id.id
    #                 qty = bom_line.product_qty
    #                 moves.append(production._get_move_raw_values(
    #                     bom_line.product_id,
    #                     factor*qty,
    #                     bom_line.product_uom_id,
    #                     operation,
    #                     bom_line
    #                 ))
    #     return moves