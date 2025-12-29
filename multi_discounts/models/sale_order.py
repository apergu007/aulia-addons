from odoo import api, fields, models, _
import re


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    multi_discount = fields.Char(
        string='Discounts Multi',
        help="Multiple discounts, separated by '+' sign. "
             "Example:\n"
             "- Percent: 10+5 (means 10% then 5%)\n"
             "- Amount: 10000+5000 (means Rp10.000 then Rp5.000)"
    )
    discount_type = fields.Selection(
        [('percent', 'Percentage'), ('amount', 'Amount')],
        string='Discount type',
        default='percent',
        help="How the discount values are interpreted."
    )

    @api.depends(
        'multi_discount',
        'discount_type',
        'price_unit',
        'product_uom_qty',
        'product_id',
        'order_id.partner_id',
        'order_id.currency_id',
        'order_id.company_id',
    )
    def _compute_amount(self):
        """Extend original _compute_amount."""
        for line in self:
            if line.multi_discount:
                line.discount = line._convert_multi_discount()
        super()._compute_amount()

    @api.onchange('multi_discount', 'discount_type')
    def _onchange_multi_discount(self):
        """Validate and auto-convert when user inputs multi_discount"""
        if self.multi_discount:
            # hanya angka dan + yang boleh
            if not re.match(r'^(\d+(\.\d+)?)(\+\d+(\.\d+)?)*$', self.multi_discount.strip()):
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('Invalid discount format. '
                                     'Use numbers separated by + sign (e.g. 10+5+2)')
                    }
                }
            self.discount = self._convert_multi_discount()

    # -----------------------
    # HELPERS
    # -----------------------
    def _convert_multi_discount(self):
        """
        Convert multi_discount to a single equivalent discount.
        - If type == percent: treat values as % chain (10+5 means 10% then 5%)
        - If type == amount: treat values as absolute reductions (1000+500 means Rp1500 off)
        """
        self.ensure_one()
        price = self.price_unit
        if not price:
            return 0.0

        discounts = [float(x) for x in self.multi_discount.replace(' ', '').split('+') if x]

        if self.discount_type == 'percent':
            final_price = price
            for d in discounts:
                final_price *= (1 - d / 100.0)
            return (1 - (final_price / price)) * 100.0

        elif self.discount_type == 'amount':
            total_discount = sum(discounts)
            # konversi ke persentase supaya kompatibel dengan field standard `discount`
            return min((total_discount / price) * 100.0, 100.0)

        return 0.0
