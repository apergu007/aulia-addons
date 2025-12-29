# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Waiting Approval'),
        ('approved', 'Approved'),
    ], string='Approval State', default='draft')

    def _check_receipt_tolerances(self):
        msgs = []
        for move in self.move_ids_without_package:
            if not move.product_id:
                continue
            product = move.product_id
            if not product.tolerance_value:
                continue

            ordered_qty = move.purchase_line_id.product_qty if move.purchase_line_id else move.product_uom_qty
            received_qty = sum(move.move_line_ids.mapped('quantity'))

            if product.tolerance_type == 'percent' and ordered_qty > 0:
                diff_percent = ((received_qty - ordered_qty) / ordered_qty) * 100.0
                if diff_percent > product.tolerance_value:
                    msgs.append(_(
                        '%s: received %.2f vs ordered %.2f (%.2f%%) > allowed %.2f%%'
                    ) % (product.display_name, received_qty, ordered_qty, diff_percent, product.tolerance_value))
            elif product.tolerance_type == 'fixed':
                diff_qty = received_qty - ordered_qty
                if diff_qty > product.tolerance_value:
                    msgs.append(_(
                        '%s: received %.2f vs ordered %.2f (diff %.2f) > allowed %.2f'
                    ) % (product.display_name, received_qty, ordered_qty, diff_qty, product.tolerance_value))
        return msgs

    def button_validate(self):
        for picking in self:
            if picking.picking_type_code != 'incoming':
                continue
            if picking.approval_state == 'approved':
                continue

            msgs = picking._check_receipt_tolerances()
            if msgs:
                picking.approval_state = 'to_approve'
                self.env.cr.commit()

                detail = '\n'.join(msgs)
                return {
                    'name': _('Receiving exceeds tolerance'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'picking.warning.wizard',
                    'target': 'new',
                    'context': {
                        'default_message': _(
                            'Receiving exceeds tolerance for these products:\n%s\n\n'
                            'Please ask a manager to approve this picking.'
                        ) % detail
                    }
                }
            # if msgs:
            #     # Set state dulu
            #     picking.approval_state = 'to_approve'
            #     self.env.cr.commit()  # <-- Tambahkan ini supaya perubahan tidak hilang

            #     detail = '\n'.join(msgs)
            #     # Stop proses dengan warning
            #     raise UserError(_(
            #         'Receiving exceeds tolerance for these products:\n%s\n\n'
            #         'Please ask a manager to approve this picking.'
            #     ) % detail)

        return super().button_validate()

    def action_approve_picking(self):
        self.ensure_one()
        self.write({'approval_state': 'approved'})
        return self.button_validate()

    def action_reject_picking(self):
        self.write({'approval_state': 'draft'})
        return True
