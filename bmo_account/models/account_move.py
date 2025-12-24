from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler'),('jasa', 'Jasa'),
        ], string='Types')
    
    faktur_pajak = fields.Boolean('Faktur Pajak')
    po_ttd = fields.Boolean('PO yang ditandatangani')
    surat_jalan = fields.Boolean('Surat Jalan')
    vendor_bill = fields.Boolean('Tagihan dari Vendor')
    using_auto_complete = fields.Boolean('Using Auto Complete?', default=False)

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        res = super(AccountMove, self)._onchange_purchase_auto_complete()
        if self.partner_id:
            self.using_auto_complete = True
        return res

    def action_post(self):
        for rec in self: 
            if rec.move_type == 'in_invoice':
            # if self.using_auto_complete:
                l_doc = [rec.faktur_pajak, rec.po_ttd, rec.surat_jalan, rec.vendor_bill]
                if False in l_doc:
                    raise ValidationError(_("Document Check Belum Terpenuhi"))
        return super(AccountMove, self).action_post()