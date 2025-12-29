from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    blocking_mrp_id = fields.Many2one('mrp.production', readonly=True)
    blocking_picking_id = fields.Many2one('stock.picking', readonly=True)

    @api.depends('move_raw_ids.state')
    def _compute_blocking_documents(self):
        for mo in self:
            mo.blocking_mrp_id = False
            mo.blocking_picking_id = False

            for move in mo.move_raw_ids:
                for src in move.move_dest_ids:
                    if src.state not in ('done', 'cancel'):
                        if src.raw_material_production_id:
                            mo.blocking_mrp_id = src.raw_material_production_id
                        elif src.picking_id:
                            mo.blocking_picking_id = src.picking_id
                        break

    def action_open_blocking_document(self):
        self.ensure_one()
        if self.blocking_mrp_id:
            return self.blocking_mrp_id.get_formview_action()
        if self.blocking_picking_id:
            return self.blocking_picking_id.get_formview_action()
        return {'type': 'ir.actions.act_window_close'}
