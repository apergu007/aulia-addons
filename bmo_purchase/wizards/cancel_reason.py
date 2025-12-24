
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WizardReasonCancel(models.TransientModel):
    _name = "wizard.reason.cancel"
    _description = "Wizard Reason"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    pr_id = fields.Many2one("purchase.request", string="PR", store=True)
    po_id = fields.Many2one("purchase.order", string="PO", store=True)
    reason = fields.Text('Reason')

    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self._context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'purchase.request':
            res["pr_id"] = active_id
        elif active_model == 'purchase.order':
            res["po_id"] = active_id
        return res
    
    def action_refuse_reason(self):
        for rec in self:
            if not rec.reason:
                raise  ValidationError(_("Reason Reject Must Be Filled In"))
            po_pr = rec.pr_id or rec.po_id              
            if po_pr:
                if self.pr_id:
                    po_pr.button_rejected()
                if self.po_id:
                    po_pr.button_cancel()
                po_pr.message_post(body=f"Alasan Reject: {rec.reason}", message_type='comment')
                return {'type': 'ir.actions.act_window_close'}