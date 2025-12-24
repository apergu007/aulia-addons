from odoo import models, fields, _, api

class PickingWarningWizard(models.TransientModel):
    _name = 'picking.warning.wizard'
    _description = 'Picking Warning Wizard'

    message = fields.Text(string="Warning Message", readonly=True)

    def action_confirm(self):
        # Setelah user klik OK, reload view
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
