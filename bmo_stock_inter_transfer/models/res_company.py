from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    inter_locations_clearing_account_id = fields.Many2one('account.account', string='Inter-locations Clearing Account')
