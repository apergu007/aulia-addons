from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    blocking_mrp_id = fields.Many2one('mrp.production', readonly=True)
    blocking_picking_id = fields.Many2one('stock.picking', readonly=True)

    @api.depends('move_ids_without_package.state')
    def _compute_blocking_documents(self):
        for pick in self:
            pick.blocking_mrp_id = False
            pick.blocking_picking_id = False

            for move in pick.move_ids_without_package:
                for src in move.move_dest_ids:
                    if src.state not in ('done', 'cancel'):
                        if src.raw_material_production_id:
                            pick.blocking_mrp_id = src.raw_material_production_id
                        elif src.picking_id:
                            pick.blocking_picking_id = src.picking_id
                        break

    def action_open_blocking_picking(self):
        self.ensure_one()
        if self.blocking_mrp_id:
            return self.blocking_mrp_id.get_formview_action()
        if self.blocking_picking_id:
            return self.blocking_picking_id.get_formview_action()
        return {'type': 'ir.actions.act_window_close'}
