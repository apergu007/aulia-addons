from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    saldo_active = fields.Boolean('Aktif Saldo')
    ar_value = fields.Monetary('Saldo Aging', compute="_compute_ar_value")
    saldo_limit = fields.Monetary('Saldo Limit', tracking=True)
    saldo_sisa = fields.Monetary('Sisa Saldo', compute="_compute_ar_value")
    employee_id = fields.Many2one('hr.employee', 'Salesperson')
    
    @api.depends('total_invoiced','property_account_receivable_id','saldo_limit')
    def _compute_ar_value(self):
        for p in self:
            val = 0
            if p.total_invoiced != 0:
                aml_src = self.env['account.move.line'].search([('partner_id','=',p.id),('account_id','=',p.property_account_receivable_id.id),('move_id.state','=','posted')])
                val = sum(aml_src.mapped('balance'))
            p.ar_value = val    
            p.saldo_sisa = p.saldo_limit - val