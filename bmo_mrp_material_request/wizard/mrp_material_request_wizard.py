
from odoo import models, fields, api

class MaterialRequestWizard(models.TransientModel):
    _name = 'mrp.material.request.wizard'
    _description = 'Wizard for Material Request'

    production_id = fields.Many2one('mrp.production')

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        required=True,
        default=lambda self: self.env.ref('stock.picking_type_internal').id,
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        required=True
    )

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True
    )

    line_ids = fields.One2many(
        'mrp.material.request.wizard.line',
        'wizard_id',
        string='Request Lines'
    )

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id:
            self.location_id = self.picking_type_id.default_location_src_id.id
            self.location_dest_id = self.picking_type_id.default_location_dest_id.id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        production = self.env['mrp.production'].browse(
            self.env.context.get('default_production_id')
        )

        lines = []
        for move in production.move_raw_ids:
            lines.append((0, 0, {
                'product_id': move.product_id.id,
                'qty': move.product_uom_qty,
                'uom_id': move.product_uom.id,
            }))

        res['line_ids'] = lines

        picking_type = self.env.ref('stock.picking_type_internal')
        res['location_id'] = picking_type.default_location_src_id.id
        res['location_dest_id'] = picking_type.default_location_dest_id.id
        return res

    def action_confirm(self):
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'origin': self.production_id.name,
            'group_id' : self.production_id.procurement_group_id.id,
        })

        for line in self.line_ids:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.qty,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'group_id' : self.production_id.procurement_group_id.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
        }


class MaterialRequestWizardLine(models.TransientModel):
    _name = 'mrp.material.request.wizard.line'
    _description = 'Material Request Line'

    wizard_id = fields.Many2one('mrp.material.request.wizard')
    product_id = fields.Many2one('product.product', required=True)
    qty = fields.Float(required=True)
    uom_id = fields.Many2one('uom.uom', required=True)
