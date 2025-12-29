# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('to_approve', "To Approve"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    sale_order_approval_route = fields.Selection(
        related='company_id.sale_order_approval_route', string="Use Approval Route", readonly=True)
    sale_team_id = fields.Many2one("approval.sales.team", string="Sales Teams", ondelete="restrict")
    approver_ids = fields.One2many(
        comodel_name="sale.order.approver", inverse_name="order_id", string="Approvers", readonly=True)
    current_approver = fields.Many2one(
        comodel_name="sale.order.approver", string="Approver", compute="_compute_approver", store=True, compute_sudo=True)
    next_approver = fields.Many2one(
        comodel_name="sale.order.approver", string="Next Approver", compute="_compute_approver", store=True, compute_sudo=True)
    is_current_approver = fields.Boolean(
        string="Is Current Approver", compute="_compute_is_current_approver")
    lock_amount_total = fields.Boolean(
        string="Lock Amount Total", compute="_compute_lock_amount_total")
    amount_total = fields.Monetary(tracking=True)
    so_status = fields.Char(string="PO Status", compute="_compute_so_status")

    @api.onchange('company_id')
    def _onchange_sale_team_id(self):
        if self.company_id:
            team = self.env['approval.sales.team'].search([('company_id', '=', self.company_id.id), ('active', '=', True)], limit=1)
            if team:
                self.sale_team_id = team.id
            else:
                self.sale_team_id = False

    # Method added by Vishal
    @api.depends('state', 'approver_ids', 'approver_ids.state')
    def _compute_so_status(self):
        for record in self:
            record.so_status = ''
            if record.sale_team_id and record.approver_ids:
                if record.state == 'to_approve':
                    for approver in record.approver_ids:
                        if approver.state == 'pending':
                            record.so_status = approver.role
                            continue
                else:
                    record.so_status = str(dict(record._fields['state'].selection).get(record.state))

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'amount_total' in init_values and self.amount_total != init_values.get('amount_total'):
            self._check_lock_amount_total()
        return super(SaleOrder, self)._track_subtype(init_values)


    def generate_approval_route(self):
        for order in self:
            if not order.sale_team_id:
                continue
            if order.approver_ids:
                order.approver_ids.unlink()
            for team_approver in order.sale_team_id.approver_ids:
                min_amount = team_approver.company_currency_id._convert(
                    team_approver.min_amount,
                    order.currency_id,
                    order.company_id,
                    order.date_order or fields.Date.today()
                )
                if order.amount_total >= min_amount:
                    self.env['sale.order.approver'].create({
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

    @api.depends('approver_ids.state')
    def _compute_approver(self):
        for order in self:
            next_approvers = order.approver_ids.filtered(lambda a: a.state == "to_approve")
            order.next_approver = next_approvers[0] if next_approvers else False

            current_approvers = order.approver_ids.filtered(lambda a: a.state == "pending")
            order.current_approver = current_approvers[0] if current_approvers else False

    @api.depends('current_approver','state')
    def _compute_is_current_approver(self):
        for order in self:
            appv = False
            if order.state not in ['draft','sent','sale','cancel']:
                appv = ((order.current_approver and order.current_approver.user_id == self.env.user) or self.env.is_superuser())
            order.is_current_approver = appv

    @api.depends('approver_ids.state', 'approver_ids.lock_amount_total')
    def _compute_lock_amount_total(self):
        for order in self:
            order.lock_amount_total = len(order.approver_ids.filtered(lambda a: a.state == "approved" and a.lock_amount_total)) > 0

    def send_to_approve(self):
        for order in self:
            if order.state != 'to_approve' and not order.sale_team_id:
                continue

            main_error_msg = _("Unable to send approval request to next approver.")
            if order.current_approver:
                reason_msg = _("The order must be approved by %s") % order.current_approver.user_id.name
                raise UserError("%s %s" % (main_error_msg, reason_msg))

            if not order.next_approver:
                reason_msg = _("There are no approvers in the selected PO team.")
                raise UserError("%s %s" % (main_error_msg, reason_msg))
            # use sudo as purchase user cannot update sale.order.approver
            order.sudo().next_approver.state = 'pending'
            # Now next approver became as current
            current_approver_partner = order.current_approver.user_id.partner_id
            if current_approver_partner not in order.message_partner_ids:
                order.message_subscribe([current_approver_partner.id])

    def _check_lock_amount_total(self):
        msg = _('Sorry, you are not allowed to change Amount Total of PO. ')
        for order in self:
            if order.state in ('draft', 'sent'):
                continue
            # if order.lock_amount_total:
            #     reason = _('It is locked after received approval. ')
            #     raise UserError(msg + "\n\n" + reason)
            if order.sale_team_id.lock_amount_total:
                reason = _('It is locked after generated approval route. ')
                suggestion = _('To make changes, cancel and reset PO to draft. ')
                raise UserError(msg + "\n\n" + reason + "\n\n" + suggestion)

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        if self.state not in {'draft', 'to_approve', 'sent'}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(
            not line.display_type
            and not line.is_downpayment
            and not line.product_id
            for line in self.order_line
        ):
            return _("A line on these orders missing a product, you cannot confirm it.")

        return False

    def button_approve(self):
        for order in self:
            if not order.team_id:
                # Do default behaviour if PO Team is not set
                super(SaleOrder, order).action_confirm()
            elif order.current_approver:
                if order.current_approver.user_id == self.env.user or self.env.is_superuser():
                    # If current user is current approver (or superuser) update state as "approved"
                    order.current_approver.state = 'approved'
                    order.message_post(body=_('PO approved by %s') % self.env.user.name)
                    # Check is there is another approver
                    if order.next_approver:
                        # Send request to approve is there is next approver
                        order.send_to_approve()
                    else:
                        # If there is not next approval, than assume that approval is finished and send notification
                        partner = order.user_id.partner_id if order.user_id else order.create_uid.partner_id
                        return super(SaleOrder, order).action_confirm()
            else:
                # approel Rules tirak Memenuhi syarat jalan kan seperti default
                super(SaleOrder, order).action_confirm()

    def action_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue

            if not order.team_id:
                super(SaleOrder, order).action_confirm()
            else:
                order.generate_approval_route()
                if order.next_approver:
                    order.write({'state': 'to_approve'})
                    order.send_to_approve()
                else:
                    super(SaleOrder, order).action_confirm()
                    
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True