# -*- coding: utf-8 -*-
import json
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler'),('jasa', 'Jasa'),
        ], string='PR Type')
    
    p_categ = fields.Selection([
        ('bahan_baku', 'Bahan Baku'),('bahan_kemas', 'Bahan Kemas'),
        ('lain', 'Lain Lain'),
        ], string='Purchase Category')
    from_pr = fields.Boolean('From PR?')
    
    po_teams_domain = fields.Char(
        compute="_compute_teams_domain", readonly=True)
    
    @api.depends('types','company_id')
    def _compute_teams_domain(self):
        for rec in self:
            domain = []
            if rec.types:
                po_team = self.env['purchase.team'].search([('types','=',rec.types)])
                if po_team:
                    domain += [('id','in',po_team.ids)]
            rec.po_teams_domain = json.dumps(domain)
    
    @api.onchange('types')
    def _onchange_types(self):
        for k in self:
            if k.types and not k.from_pr:
                k.team_id = False
    
    @api.onchange('types','p_categ')
    def _onchange_for_picking_type(self):
        for k in self:
            if k.types and k.p_categ:
                po_deliv = self.env['po.delivery.to'].search([('types','=',k.types),('p_categ','=',k.p_categ)])
                if not po_deliv:
                    raise ValidationError(_("Config Delivery To Belum Ada"))
                if len(po_deliv)>1:
                    raise ValidationError(_("PO Deliv Lebih Dari 1"))
                k.picking_type_id = po_deliv.picking_type_id.id
    
    # @api.onchange('company_id','types')
    # def _onchange_types(self):
    #     for rec in self:
    #         if rec.types:
    #             team_src = self.env['purchase.team']
    #             team_id = team_src.search([('company_id','=',rec.company_id.id),('types','=',rec.types)])
    #             rec.team_id = team_id.id

    def wizard_pop_up_cancel(self):
        if self.state in ['purchase','done']:
            raise UserError(
                _("You cannot Reject a purchase request which is not draft.")
            )
        return {
			'name': "Reason Reject",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'wizard.reason.cancel',
			'view_id': self.env.ref('bmo_purchase.wizard_reason_cancel_form').id,
			'target': 'new',
		}
    
    # def button_cancel(self):
    #     super(PurchaseOrder, self).button_cancel()
    #     if self.state in ['purchase','done']:
    #         raise UserError(
    #             _("You cannot Reject a purchase request which is not draft.")
    #         )
    #     return self.wizard_pop_up_cancel()

    # dimatikan dlu buat migrasi
    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(PurchaseOrder, self).create(vals_list)
    #     for rec in res: 
    #         if rec.p_categ == 'bahan_baku':
    #             code = 'po.bahan.baku'
    #         elif rec.p_categ == 'bahan_kemas':
    #             code = 'po.bahan.kemas'
    #         else:
    #             code = 'po.lain.lain'
    #         seq_src = self.env['ir.sequence'].search([('code','=',code)])
    #         rec.name = seq_src.next_by_id()
    #     return res

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    description = fields.Char('Description')


    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        vals = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        vals.update({
            'po_line_id': self.id,
        })
        return vals

    # def _prepare_account_move_line(self, move=False):
    #     vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
    #     vals.update({
    #         'discount': 0,
    #         'discount_type': 'percent',
    #         'multi_discount': self.discount,
    #     })
    #     return vals