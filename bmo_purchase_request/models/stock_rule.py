from odoo import api, fields, models, _
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_buy(self, procurements):
        """Override stock.rule buy: buat Purchase Request, bukan PO."""
        PurchaseRequest = self.env['purchase.request']
        PurchaseRequestLine = self.env['purchase.request.line']

        # Grouping key = (company, date_planned, origin, group_id)
        pr_groups = {}

        for procurement, rule in procurements:
            values = procurement.values or {}
            company = procurement.company_id
            product = procurement.product_id
            qty = procurement.product_qty
            uom = procurement.product_uom
            location = procurement.location_id
            origin = procurement.origin
            name = procurement.name
            group = values.get('group_id')  # << ambil dari procurement.values

            # Hitung date_planned
            date_planned = values.get('date_planned') or fields.Date.context_today(self)

            # Cek apakah sudah ada PR line untuk group_id ini
            existing_line = PurchaseRequestLine.search([
                ('product_id', '=', product.id),
                ('group_id', '=', group.id if group else False),
                ('request_id.company_id', '=', company.id),
            ], limit=1)
            if existing_line:
                _logger.info("Skip PR line, sudah ada untuk product %s & group %s", product.display_name, group.display_name if group else '-')
                continue

            key = (company.id, date_planned, origin, group and group.id or False)
            if key not in pr_groups:
                pr_vals = {
                    'company_id': company.id,
                    'origin': origin,
                    'date_start': date_planned,
                    'requested_by': self.env.user.id,
                    'group_id': group and group.id or False,
                }
                pr = PurchaseRequest.create(pr_vals)
                pr_groups[key] = pr
                _logger.info("Created new Purchase Request %s (group_id=%s)", pr.name, group.display_name if group else '-')
            else:
                pr = pr_groups[key]

            # Tambahkan line
            line_vals = {
                'request_id': pr.id,
                'product_id': product.id,
                'product_uom_id': uom.id,
                'product_qty': qty,
                'name': name,
                'group_id': group and group.id or False,
                'company_id': company.id,
                'date_required': date_planned,
            }
            PurchaseRequestLine.create(line_vals)
            _logger.info("Added PR line for %s (group_id=%s)", product.display_name, group.display_name if group else '-')

        return True
