
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WizardConfirmation(models.TransientModel):
    _name = "wizard.confirmation"
    _description = "Wizard Confirmation Qty"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    char_confirm = fields.Char(string='Apakah Anda Yakin memproduksi dibawah Qty BOm')
    mo_id = fields.Many2one("mrp.production", string="PR", store=True)
    reason = fields.Text('Reason')
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self._context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'mrp.production':
            res["mo_id"] = active_id
        return res

    def action_confirm(self):
        for rec in self:
            rec.mo_id.message_post(body=f"Alasan: {rec.reason}", message_type='comment')
            # rec.mo_id.is_qty_ok = True
            rec.mo_id.write({'is_qty_ok': True})

            # rec.mo_id.with_context(skip_backorder=True).button_mark_done()

            return rec.mo_id.button_mark_done()
        # return {'type': 'ir.actions.act_window_close'}