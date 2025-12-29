from odoo import api, fields, models, _

class PurchaseTeam(models.Model):
    _inherit = "purchase.team"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler'),('jasa', 'Jasa'),
        ], string='PO Type')

class PurchaseRequestTeam(models.Model):
    _inherit = "purchase.request.team"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler')
        ], string='PR Type')