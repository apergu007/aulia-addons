from odoo import fields, models, api, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    active = fields.Boolean(default=True)