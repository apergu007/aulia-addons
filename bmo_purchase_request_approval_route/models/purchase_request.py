# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.model
    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return types[:1]

    name = fields.Char(
        string="Request Reference", required=False, default=lambda self: _("New"), tracking=True,)
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="Picking Type", required=False, default=_default_picking_type,)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(PurchaseRequest, self).create(vals_list)
    #     if not res.line_ids:
    #         raise ValidationError(_('Item Details Must Be Filled In'))
    #     return res
    
    @api.depends('line_ids')
    def _compute_state(self):
        for pr in self:
            if any(line.purchased_qty >= line.product_qty for line in pr.line_ids):
                pr.write({"state": "done"})


    # PR Team ============================
    team_id = fields.Many2one(
        comodel_name="purchase.request.team", string="PR Team", ondelete="restrict", )
    approver_ids = fields.One2many(
        comodel_name="purchase.request.approver", inverse_name="order_id", string="Approvers", readonly=True)
    current_approver = fields.Many2one(
        comodel_name="purchase.request.approver", string="Current Approver", compute="_compute_approver", store=True, compute_sudo=True)

    next_approver = fields.Many2one(
        comodel_name="purchase.request.approver", string="Next Approver", compute="_compute_approver", store=True, compute_sudo=True)

    is_current_approver = fields.Boolean(
        string="Is Current Approver", compute="_compute_is_current_approver")

    lock_amount_total = fields.Boolean(
        string="Lock Amount Total", compute="_compute_lock_amount_total")
    
    @api.onchange('company_id')
    def _onchange_team_approver(self):
        self.team_id = self.env['purchase.request.team'].search([('company_id','=',self.company_id.id)], limit=1)

    @api.depends('approver_ids.state')
    def _compute_approver(self):
        for order in self:
            next_approvers = order.approver_ids.filtered(lambda a: a.state == "to approve")
            order.next_approver = next_approvers[0] if next_approvers else False

            current_approvers = order.approver_ids.filtered(lambda a: a.state == "pending")
            order.current_approver = current_approvers[0] if current_approvers else False

    @api.depends('current_approver','state')
    def _compute_is_current_approver(self):
        for order in self:
            appr = False
            if order.state not in ['rejected', 'draft']:
                appr = ((order.current_approver and order.current_approver.user_id == self.env.user) or self.env.is_superuser())
            order.is_current_approver = appr
    
    @api.depends('approver_ids.state', 'approver_ids.lock_amount_total')
    def _compute_lock_amount_total(self):
        for order in self:
            order.lock_amount_total = len(order.approver_ids.filtered(lambda a: a.state == "approved" and a.lock_amount_total)) > 0        
    
    def generate_approval_route(self):
        """
        Generate approval route for order Request
        :return:
        """
        for order in self:
            if not order.team_id:
                continue
            if order.approver_ids:
                # reset approval route
                order.approver_ids.unlink()
            for team_approver in order.team_id.approver_ids:
                min_amount = team_approver.company_currency_id._convert(
                    team_approver.min_amount,
                    order.currency_id,
                    order.company_id,
                    order.date_start or fields.Date.today()
                )
                if order.estimated_cost >= min_amount:
                    self.env['purchase.request.approver'].create({
                        'sequence': team_approver.sequence,
                        'team_id': team_approver.team_id.id,
                        'user_id': team_approver.user_id.id,
                        'role': team_approver.role,
                        'min_amount': team_approver.min_amount,
                        'max_amount': team_approver.max_amount,
                        'lock_amount_total': team_approver.lock_amount_total,
                        'order_id': order.id,
                        'team_approver_id': team_approver.id,
                    })

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(PurchaseRequest, self).create(vals_list)
    #     for rec in res: 
    #         ou_seq_src = self.env['operating.unit.sequence'].find_sequence(rec._name, rec.operating_unit_id, True, 'PR', rec.date_start)
    #         rec.name = ou_seq_src.next_by_id(sequence_date=rec.date_start)
    #     return res
    
    def send_to_approve(self):
        for order in self:
            if order.state != 'to approve' and not order.team_id:
                continue

            main_error_msg = _("Unable to send approval request to next approver.")
            if order.current_approver:
                reason_msg = _("The order must be approved by %s") % order.current_approver.user_id.name
                raise ValidationError("%s %s" % (main_error_msg, reason_msg))

            if not order.next_approver:
                reason_msg = _("There are no approvers in the selected PO team.")
                raise ValidationError("%s %s" % (main_error_msg, reason_msg))
            # use sudo as purchase user cannot update purchase.order.approver
            order.sudo().next_approver.state = 'pending'
            # Now next approver became as current
            current_approver_partner = order.current_approver.user_id.partner_id
            if current_approver_partner not in order.message_partner_ids:
                order.message_subscribe([current_approver_partner.id])

    def button_to_approve(self):
        for order in self:
            if order.state != 'draft':
                continue
            if not order.team_id:
                raise ValidationError(_('Team Approvel Not yet created'))
            else:
                order.generate_approval_route()
                if order.next_approver:
                    order.write({'state': 'to_approve'})
                    order.send_to_approve()
                else:
                    order.write({'state': 'approved'})
        return True
    
    def button_approved(self, force=False):
        for order in self:
            if order.current_approver:
                if order.current_approver.user_id == self.env.user or self.env.is_superuser():
                    order.current_approver.state = 'approved'
                    order.message_post(body=_('PO approved by %s') % self.env.user.name)
                    if order.next_approver:
                        order.send_to_approve()
                    else:
                        order.write({'state': 'approved'})