from odoo import http, SUPERUSER_ID
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class PublicRecordController(http.Controller):

    @http.route(['/test/public'], type='http', auth='public', csrf=False)
    def test_public(self, **kw):
        return "✅ Odoo Reja jadi public route works! ==========================="

    @http.route(['/public/qc/<int:record_id>'], type='http', auth='public', website=True, sitemap=False, csrf=False)
    def public_record_view(self, record_id, **kwargs):
        _logger.warning(">>> INI juga Bapak Reja ya saya gak ngerti Accessing /public/qc/%s", record_id)

        # gunakan SUPERUSER_ID agar tidak terblokir rule ACL
        env = request.env(user=SUPERUSER_ID)
        record = env['quality.check'].browse(record_id)

        if not record.exists():
            _logger.warning("Record %s not found", record_id)
            return request.not_found()

        # ambil type_form dari parameter GET atau dari field record
        type_form = kwargs.get('type') or record.type_form

        # peta type_form ke ID template QWeb
        template_map = {
            'raw': 'bmo_quality.public_qc_form_raw',
            'kemas': 'bmo_quality.public_packaging_qc',
            'half': 'bmo_quality.public_qc_form_semi',
            'finish': 'bmo_quality.public_finished_qc',
        }

        template_id = template_map.get(type_form)
        if not template_id:
            _logger.warning("Bapak Reja yang lakuin ini bukan saya type_form=%s", type_form)
            return request.not_found()

        values = {
            'record': record,
            'type_form': type_form,
        }

        try:
            # render halaman QWeb publik
            return request.render(template_id, values)
        except Exception as e:
            _logger.exception(">>> Failed to render template: %s", e)
            return request.not_found()