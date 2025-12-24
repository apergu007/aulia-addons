# -*- coding: utf-8 -*-
import json
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler'),
        ], string='PR Type')
    
    p_categ = fields.Selection([
        ('bahan_baku', 'Bahan Baku'),('bahan_kemas', 'Bahan Kemas'),
        ('lain', 'Lain Lain'),
        ], string='Purchase Category')
    
    pr_teams_domain = fields.Char(
        compute="_compute_teams_domain", readonly=True)
    origin_text = fields.Text('Source Document', compute="_compute_origin_text")
    to_done = fields.Integer('To Done', compute="_compute_to_done")

    @api.depends('line_ids.product_qty', 'line_ids.purchased_qty','state')
    def _compute_to_done(self):
        for rec in self:
            all_done = all(
                line.product_qty == line.purchased_qty
                for line in rec.line_ids
            )
            rec.to_done = all_done
            if rec.state == 'approved' and all_done:
                rec.state = 'done'


    @api.depends('origin')
    def _compute_origin_text(self):
        for rec in self:
            text = ""
            if rec.origin:
                origin_list = rec.origin.split(',')
                grouped = []
                for i in range(0, len(origin_list), 4):
                    chunk = origin_list[i:i+8]
                    grouped.append(", ".join(chunk))
                text = "\n".join(grouped)
            rec.origin_text = text
    
    @api.depends('types','company_id')
    def _compute_teams_domain(self):
        for rec in self:
            domain = []
            if rec.types:
                pr_team = self.env['purchase.request.team'].search([('types','=',rec.types)])
                if pr_team:
                    domain += [('id','in',pr_team.ids)]
            rec.pr_teams_domain = json.dumps(domain)
    
    @api.onchange('types')
    def _onchange_types(self):
        for k in self:
            if k.types:
                k.team_id = False
    
    
    # def button_rejected(self):
    #     super(PurchaseRequest, self).button_rejected()
    #     p_state = self.line_ids.mapped("purchased_qty")
    #     if sum(p_state) != 0:
    #         if 'draft' not in self.line_ids.mapped("purchase_state"):
    #             raise UserError(
    #                 _("You cannot Reject a purchase request which is not draft.")
    #             )
    #     return self.wizard_pop_up_cancel()
    
    def wizard_pop_up_cancel(self):
        p_state = self.line_ids.mapped("purchased_qty")
        if sum(p_state) != 0:
            if 'draft' not in self.line_ids.mapped("purchase_state"):
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
    
    # @api.onchange('company_id','types')
    # def _onchange_types(self):
    #     for rec in self:
    #         if rec.types:
    #             team_pr_src = self.env['purchase.request.team']
    #             team_id = team_pr_src.search([('company_id','=',rec.company_id.id),('types','=',rec.types)])
    #             rec.team_id = team_id.id
    
class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        tracking=True,
    )
    categ_domain = fields.Char(
        compute="_compute_categ_domain", readonly=True)
    last_po = fields.Float('Last PO Qty', compute="_compute_last_po", readonly=True)
    p_categ = fields.Selection([
        ('bahan_baku', 'Bahan Baku'),('bahan_kemas', 'Bahan Kemas'),
        ('lain', 'Lain Lain'),
        ], string='Purchase Category')
    product_categ_id = fields.Many2one('product.category', 'Product Category', related="product_id.categ_id")
    last_po_price = fields.Float('Last PO Price', compute="_compute_last_po_price", readonly=True)

    @api.depends('product_id')
    def _compute_last_po_price(self):
        for rec in self:
            price = 0
            if rec.product_id:
                po_line_src = self.env['purchase.order.line'].search([('product_id','=',rec.product_id.id),('order_id.state','in',['purchase','done'])])
                if po_line_src:
                    pol = po_line_src.sorted(key=lambda pol: pol.order_id.date_approve)
                    price = pol[-1].price_unit
            rec.last_po_price = price

    @api.depends('request_id.types','company_id')
    def _compute_categ_domain(self):
        for rec in self:
            domain = []
            if rec.request_id.types:
                categ_src = self.env['product.category'].search([('types','=',rec.request_id.types)])
                if categ_src:
                    domain += [('categ_id','in',categ_src.ids)]
            rec.categ_domain = json.dumps(domain)
    
    @api.depends('product_id')
    def _compute_last_po(self):
        for rec in self:
            qty = 0
            if rec.product_id:
                po_line_src = self.env['purchase.order.line'].search([('product_id','=',rec.product_id.id),('order_id.state','in',['purchase','done'])])
                if po_line_src:
                    pol = po_line_src.sorted(key=lambda pol: pol.order_id.date_approve)
                    qty = pol[-1].product_qty
            rec.last_po = qty
