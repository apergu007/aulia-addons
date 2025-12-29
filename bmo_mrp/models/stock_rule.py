from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import float_compare, OrderedSet

import logging
_logger = logging.getLogger(__name__)

class ProcurementGroupCustom(models.Model):
    _inherit = "procurement.group"

    def _get_rule(self, product_id, location_id, values):
        rule = super()._get_rule(product_id, location_id, values)
        company = values.get("company_id") or self.env.company

        # hasil _bom_find adalah dict {product: bom}
        bom_map = self.env["mrp.bom"]._bom_find(
            products=product_id,
            company_id=company.id,
            bom_type="normal",
        )
        bom = bom_map.get(product_id)

        if bom and location_id.usage != "customer":
            manuf_rules = product_id.route_ids.mapped("rule_ids").filtered(lambda r: r.action == "manufacture")
            if manuf_rules:
                manuf_rules = manuf_rules.sorted("sequence")
                rule = manuf_rules[0]
                values["bom_id"] = bom     # langsung record, jangan .id
                _logger.warning("[RULE] Product %s pakai Manufacture | BoM: %s | Rule: %s",
                                product_id.display_name, bom.display_name, rule.display_name)
        else:
            _logger.warning("[RULE] Product %s tidak ada BoM → pakai rule default: %s",
                            product_id.display_name, rule.display_name if rule else "NONE")

        return rule

class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_manufacture(self, procurements):
        new_productions_values_by_company = defaultdict(lambda: defaultdict(list))
        for procurement, rule in procurements:
            if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
                # If procurement contains negative quantity, don't create a MO that would be for a negative value.
                continue
            bom = rule._get_matching_bom(procurement.product_id, procurement.company_id, procurement.values)

            mo = self.env['mrp.production']
            if procurement.origin != 'MPS':
                domain = rule._make_mo_get_domain(procurement, bom)
                mo = self.env['mrp.production'].sudo().search(domain, limit=1)
            if not mo:
                procurement_qty = procurement.product_qty
                batch_size = procurement.values.get('batch_size', procurement_qty)
                if batch_size <= 0:
                    batch_size = procurement_qty
                vals = rule._prepare_mo_vals(*procurement, bom)
                while float_compare(procurement_qty, 0, precision_rounding=procurement.product_uom.rounding) > 0:
                    current_qty = min(procurement_qty, batch_size)
                    new_productions_values_by_company[procurement.company_id.id]['values'].append({
                        **vals,
                        'product_qty': procurement.product_uom._compute_quantity(current_qty, bom.product_uom_id) if bom else current_qty,
                    })
                    new_productions_values_by_company[procurement.company_id.id]['procurements'].append(procurement)
                    procurement_qty -= current_qty
            else:
                self.env['change.production.qty'].sudo().with_context(skip_activity=True).create({
                    'mo_id': mo.id,
                    'product_qty': mo.product_id.uom_id._compute_quantity((mo.product_uom_qty + procurement.product_qty), mo.product_uom_id)
                }).change_prod_qty()

        for company_id in new_productions_values_by_company:
            productions_vals_list = new_productions_values_by_company[company_id]['values']
            # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            productions = self.env['mrp.production'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(productions_vals_list)
            # productions.filtered(self._should_auto_confirm_procurement_mo).action_confirm()
            productions._post_run_manufacture(new_productions_values_by_company[company_id]['procurements'])
        return True