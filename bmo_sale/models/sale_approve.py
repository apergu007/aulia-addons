from odoo import fields, models, api, _


class ApprovalSalesTeam(models.Model):
    _inherit = "approval.sales.team"

    sale_type = fields.Selection([
        ('reguler', 'Reqular'),('maklon', 'Maklon'),
        ('sample', 'Sample')], string='Sales Type')
