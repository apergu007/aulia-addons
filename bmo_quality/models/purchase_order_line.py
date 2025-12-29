from odoo import api, Command, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    check_ids = fields.One2many('quality.check', 'po_line_id', 'Checks')

    def _prepare_account_move_line(self, move=False):
        for line in self:
            if line.order_id.p_categ != 'lain':
                if not line.check_ids:
                    # raise UserError(_("No Quality Check defined on this purchase order line. Please define at least one quality check."))
                    continue
                else:
                    if line.check_ids.filtered(lambda check: check.quality_state == 'none'):
                        raise UserError(_("Some quality checks are not done yet. Please complete all quality checks before receiving the products."))
                
        return super()._prepare_account_move_line(move=move)