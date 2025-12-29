from datetime import datetime
from odoo import fields, models, api, _
import json


class AccountMove(models.Model):
    _inherit = "account.move"

    picking_id = fields.Many2one('stock.picking', 'Picking')
    picking_ids = fields.Many2many('stock.picking', string='Pickings')
    picking_domain = fields.Char(
        compute="_compute_pick_domain", readonly=True)
    
    def _onchange_purchase_auto_complete(self):
        res = super(AccountMove, self)._onchange_purchase_auto_complete()
        if self.invoice_origin:
            origin = self.invoice_origin.split(',')
            self.picking_ids = False
            pol_src = self.env['purchase.order.line'].search([('order_id.name','in',origin)])
            if pol_src:
                qc_id = pol_src.check_ids.filtered(lambda qc: qc.quality_state != 'none')
                qc_src = self.env['quality.check'].browse(qc_id.ids)
                if qc_src:
                    self.picking_ids = qc_src.mapped('picking_id.id')
        return res
    
    @api.depends('invoice_origin')
    def _compute_pick_domain(self):
        for rec in self:
            domain = []
            if rec.move_type in ['in_invoice', 'in_refund']:
                domain = [('picking_type_code','=','incoming')]
            elif rec.move_type in ['out_invoice', 'out_refund']:
                domain = [('picking_type_code','=','outgoing')]
            if rec.invoice_origin:
                origin = rec.invoice_origin.split(',')
                pol_src = self.env['purchase.order.line'].search([('order_id.name','in',origin)])
                if pol_src:
                    qc_id = pol_src.check_ids.filtered(lambda qc: qc.quality_state != 'none')
                    qc_src = self.env['quality.check'].browse(qc_id.ids)
                    if qc_src:
                        domain += [('id','in',qc_src.mapped('picking_id.id'))]
            rec.picking_domain = json.dumps(domain)
