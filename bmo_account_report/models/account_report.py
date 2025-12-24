from odoo import models, fields, api, osv
from odoo.addons.web.controllers.utils import clean_action
from odoo.tools import SQL, Query


class AccountReport(models.Model):
    _inherit = "account.report"

    filter_account_ids = fields.Many2many('account.account', string='Filter Account')


    ####################################################
    # OPTIONS: Filter Account
    ####################################################
    @api.model
    def _get_options_account(self, options):
        domain = []
        report_id = self.env['account.report'].browse(options['report_id'])
        if report_id.filter_account_ids:
            domain.append(('account_id', 'in', report_id.filter_account_ids.ids))
        return domain
    

    ####################################################
    # OPTIONS: CORE
    ####################################################

    def _get_options_domain(self, options, date_scope):
        self.ensure_one()
        domain = super()._get_options_domain(options, date_scope)

        domain += self._get_options_account(options)

        return domain