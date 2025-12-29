from odoo import models, fields

class AtsDocument(models.Model):
    _name = 'ats.document'
    _description = 'User Manual dan Buku Putih'

    name = fields.Char(string="Judul", required=True)
    doc_type = fields.Selection([
        ('manual', 'User Manual'),
        ('whitepaper', 'Buku Putih'),
    ], string="Jenis Dokumen", required=True)
    file = fields.Binary(string="File", required=True)
    filename = fields.Char(string="Nama File")
    date = fields.Date(string="Tanggal Upload", default=fields.Date.today)
    uploaded_by = fields.Many2one('res.users', string="Diupload Oleh", default=lambda self: self.env.user)

    def action_open_viewer(self):
        """Buka viewer untuk melihat file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self._name}/{self.id}/file/{self.filename}?download=false",
            'target': 'new',
        }
