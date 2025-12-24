
from odoo import models

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_open_material_request_wizard(self):
        return {
            'name': 'Create Material Request',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.material.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            }
        }
