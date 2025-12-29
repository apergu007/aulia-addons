from odoo import models, fields
from odoo.exceptions import UserError
from io import BytesIO
import base64
from openpyxl import Workbook

class FakturKeluaranWizard(models.TransientModel):
    _name = 'faktur.keluaran.wizard'
    _description = 'Wizard Laporan Faktur Keluaran'

    date_from = fields.Date(required=True, string="Date From")
    date_to = fields.Date(required=True, string="Date To")
    file = fields.Binary('File', readonly=True)
    filename = fields.Char('Filename')

    def action_generate_excel(self):
        if self.date_from > self.date_to:
            raise UserError("Tanggal awal tidak boleh lebih besar dari tanggal akhir.")

        moves = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted')
        ])

        output = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Faktur Keluaran"

        headers = ['No', 'Faktur Pajak', 'No. Inv', 'Customer', 'Harga Jual', 'DPP', 'PPN']
        ws.append(headers)

        no = 1
        for m in moves:
            ws.append([
                no,
                m.l10n_id_tax_number or '',
                m.name or '',
                m.partner_id.name or '',
                m.amount_total,
                m.amount_untaxed,
                m.amount_tax,
            ])
            no += 1

        wb.save(output)
        output.seek(0)

        self.file = base64.b64encode(output.read())
        self.filename = f"Faktur_Keluaran_{self.date_from}_to_{self.date_to}.xlsx"

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'faktur.keluaran.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }
