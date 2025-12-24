from odoo import models, fields, _
from datetime import timedelta


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    def _cron_expiry_notification(self):
        """Buat notifikasi activity kalau lot mau expired"""
        today = fields.Date.today()
        soon = today + timedelta(days=7)  # notifikasi 7 hari sebelum expired

        lots = self.search([
            ('use_date', '!=', False),
            ('use_date', '<=', soon),
            ('use_date', '>=', today)
        ])

        for lot in lots:
            # Hapus dulu activity lama biar tidak dobel
            lot.activity_unlink(['mail.mail_activity_data_warning'])

            # Buat activity warning
            lot.activity_schedule(
                'mail.mail_activity_data_warning',
                user_id=lot.create_uid.id or self.env.user.id,
                note=_("Lot %s untuk produk %s akan expired pada %s") % (
                    lot.name, lot.product_id.display_name, lot.use_date
                )
            )
