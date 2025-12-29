# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_round
import re
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    multi_discount = fields.Char(
        string="Discounts (%) / Amounts",
        help="Multiple discounts separated by '+' (percent or amount depending on Discount Type). "
             "Example percent: '10+5+2'. Example amount: '100+50'."
    )
    discount_type = fields.Selection(
        [('percent', 'Percentage'), ('amount', 'Amount')],
        string='Discount Type',
        default='percent',
        help="Type of discount entered in Multi Discount field."
    )

    # Note: we intentionally do NOT override Odoo's price computes.
    # Instead we update the standard `discount` field (percentage) so Odoo computes totals normally.

    @api.model_create_multi
    def create(self, vals_list):
        # Before creating, compute and set the equivalent discount percent when possible
        for vals in vals_list:
            # copy multi_discount from related sale_line if present (M2M commands)
            if not vals.get('multi_discount'):
                sale_line_ids = vals.get('sale_line_ids')
                if sale_line_ids:
                    ids = [cmd[1] for cmd in sale_line_ids if isinstance(cmd, (list, tuple)) and cmd[0] in (4, 6)]
                    if ids:
                        sale_line = self.env['sale.order.line'].browse(ids[0])
                        if sale_line and sale_line.multi_discount:
                            vals['multi_discount'] = sale_line.multi_discount
                            # copy discount_type from sale.line if that field exists; fallback to percent
                            vals['discount_type'] = getattr(sale_line, 'discount_type', 'percent')

            # compute discount percent if multi_discount present and price_unit present
            if vals.get('multi_discount') and vals.get('price_unit') is not None:
                try:
                    discount_pct = self._compute_equivalent_discount_from_values(
                        original_price=float(vals.get('price_unit', 0.0)),
                        multi_discount_str=vals.get('multi_discount', ''),
                        discount_type=vals.get('discount_type', 'percent')
                    )
                    # store numeric value
                    vals['discount'] = discount_pct
                except Exception as e:
                    _logger.exception("Error computing multi_discount on create: %s", e)
        return super().create(vals_list)

    def write(self, vals):
        # If multi_discount, discount_type, or price_unit is updated, recompute discount percent
        need_recompute = False
        for key in ('multi_discount', 'discount_type', 'price_unit', 'quantity'):
            if key in vals:
                need_recompute = True
                break

        # handle sale_line_ids on write (commonly in invoice creation flows)
        if 'sale_line_ids' in vals and not vals.get('multi_discount'):
            sale_line_ids = vals.get('sale_line_ids')
            ids = [cmd[1] for cmd in sale_line_ids if isinstance(cmd, (list, tuple)) and cmd[0] in (4, 6)]
            if ids:
                sale_line = self.env['sale.order.line'].browse(ids[0])
                if sale_line and sale_line.multi_discount:
                    vals['multi_discount'] = sale_line.multi_discount
                    vals['discount_type'] = getattr(sale_line, 'discount_type', 'percent')
                    need_recompute = True

        if need_recompute:
            # We'll compute for each record separately if needed, using either the incoming vals or current record values
            for line in self:
                # prepare values to compute with: prefer vals (incoming), fallback to existing line
                multi_discount = vals.get('multi_discount', line.multi_discount)
                discount_type = vals.get('discount_type', line.discount_type)
                price_unit = vals.get('price_unit', line.price_unit)

                if multi_discount and price_unit is not None:
                    try:
                        discount_pct = self._compute_equivalent_discount_from_values(
                            original_price=float(price_unit),
                            multi_discount_str=multi_discount,
                            discount_type=discount_type or 'percent'
                        )
                        # apply computed discount into vals to be written (so super().write writes it)
                        # But ensure we don't override if incoming vals explicitly sets discount
                        if 'discount' not in vals:
                            # Update line via direct write to avoid side-effects: accumulate into vals for whole write
                            # We'll collect per-record writes after super call to avoid race; simpler approach:
                            # set on record immediately (safe), then call super for remaining vals.
                            # However setting then super may cause double-compute; it's acceptable and common.
                            line.discount = discount_pct
                    except Exception as e:
                        _logger.exception("Error computing multi_discount on write for line %s: %s", line.id, e)

        # finally perform the usual write for provided vals
        return super().write(vals)

    @api.onchange('multi_discount', 'discount_type', 'price_unit')
    def _onchange_multi_discount(self):
        """Validate format + compute discount percent to update UI immediately."""
        for line in self:
            if not line.multi_discount:
                # nothing to do: allow clearing
                continue

            # basic validation: allow numbers with optional decimals separated by +
            if not re.match(r'^\s*\d+(\.\d+)?(\s*\+\s*\d+(\.\d+)?)*\s*$', line.multi_discount):
                # keep simple message
                return {
                    'warning': {
                        'title': _('Invalid format'),
                        'message': _('Invalid discount format. Use numbers separated by "+" (e.g. 10+5+2 or 100+50).')
                    }
                }

            # compute equivalent discount percent (only if price_unit is available and > 0)
            if line.price_unit and float(line.price_unit) != 0.0:
                try:
                    pct = self._compute_equivalent_discount_from_values(
                        original_price=float(line.price_unit),
                        multi_discount_str=line.multi_discount,
                        discount_type=line.discount_type or 'percent'
                    )
                    # Round to reasonable precision for display
                    line.discount = float_round(pct, precision_digits=6)
                except Exception as e:
                    _logger.exception("Error in onchange multi_discount compute: %s", e)
                    # don't break UI; simply ignore

    def _compute_equivalent_discount_from_values(self, original_price, multi_discount_str, discount_type):
        """
        Return equivalent discount percentage (0-100) given original_price and multi discount string.
        - original_price: float (price_unit)
        - multi_discount_str: string like '10+5+2' or '100+50' depending on type
        - discount_type: 'percent' or 'amount'
        """
        # safety
        if not original_price or float(original_price) == 0.0:
            return 0.0

        discounts = self._parse_multi_discount(multi_discount_str)
        if not discounts:
            return 0.0

        if discount_type == 'percent':
            final_price = original_price
            for d in discounts:
                # treat each as percent, apply sequentially
                final_price = final_price * (1.0 - (float(d) / 100.0))
            # equivalent percent
            eq = (1.0 - (final_price / float(original_price))) * 100.0
            return float_round(eq, precision_digits=6)
        else:
            # amount based: subtract total fixed amounts from unit price
            total_amount = sum(float(d) for d in discounts)
            final_price = max(float(original_price) - total_amount, 0.0)
            eq = (1.0 - (final_price / float(original_price))) * 100.0
            return float_round(eq, precision_digits=6)

    def _parse_multi_discount(self, s):
        """
        Parse multi discount string and return list of floats.
        Accepts patterns like '10+5+2', ' 10 + 5 ', '100+50', '10.5+0.25'
        Returns [] if nothing valid.
        """
        if not s:
            return []
        # remove spaces
        s = s.strip()
        # split by +
        parts = [p.strip() for p in s.split('+') if p.strip() != '']
        results = []
        for p in parts:
            # accept only numeric (int or float)
            if re.match(r'^\d+(\.\d+)?$', p):
                try:
                    results.append(float(p))
                except Exception:
                    # skip invalid
                    continue
            else:
                # not matching -> try to coerce with replace comma to dot (if user used comma)
                p2 = p.replace(',', '.')
                if re.match(r'^\d+(\.\d+)?$', p2):
                    try:
                        results.append(float(p2))
                    except Exception:
                        continue
                else:
                    # skip invalid fragments
                    continue
        return results

    def _get_equivalent_discount(self, original_price, final_price):
        """
        Backward-compatible helper used in some legacy code: compute percentage given original & final price.
        """
        if not original_price or float(original_price) == 0.0:
            return 0.0
        try:
            eq = (1.0 - (float(final_price) / float(original_price))) * 100.0
            return float_round(eq, precision_digits=6)
        except Exception:
            return 0.0

    @api.model
    def _prepare_add_missing_fields(self, values):
        """Inject multi_discount from related sale.order.line when invoicing (keeps behavior from your original)."""
        values = super()._prepare_add_missing_fields(values)
        sale_line_ids = values.get('sale_line_ids')
        if sale_line_ids:
            # Extract IDs from M2M commands (4, 6)
            ids = [cmd[1] for cmd in sale_line_ids if isinstance(cmd, (list, tuple)) and cmd[0] in (4, 6)]
            if ids:
                sale_line = self.env['sale.order.line'].browse(ids[0])
                if sale_line and sale_line.multi_discount:
                    values['multi_discount'] = sale_line.multi_discount
                    # attempt to copy discount_type if sale_line define it, else keep percent
                    values['discount_type'] = getattr(sale_line, 'discount_type', 'percent')
                    # compute discount if price_unit present
                    if values.get('price_unit'):
                        try:
                            discount_pct = self._compute_equivalent_discount_from_values(
                                original_price=float(values['price_unit']),
                                multi_discount_str=values['multi_discount'],
                                discount_type=values.get('discount_type', 'percent')
                            )
                            values['discount'] = discount_pct
                        except Exception as e:
                            _logger.exception("Error computing discount in _prepare_add_missing_fields: %s", e)
        return values
