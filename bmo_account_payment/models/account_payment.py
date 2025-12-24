# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

import logging
_logger = logging.getLogger(__name__)


class AccountPaymentMultiple(models.Model):
    _name = "account.payment.multiple"
    _description = "Multiple Account Payment Line"

    name = fields.Char(string='Label')
    account_id = fields.Many2one('account.account', string='Account', domain=[('deprecated', '=', False)], copy=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Accounts')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    payment_id = fields.Many2one('account.payment', string='Payment', index=True, ondelete='cascade')
    debit = fields.Monetary(string='Debit', currency_field='currency_id')
    credit = fields.Monetary(string='Credit', currency_field='currency_id')

    @api.onchange('account_id')
    def _onchange_account_id(self):
        for line in self:
            if line.account_id:
                line.name = line.account_id.name


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Internal Transfer
    is_internal_transfer = fields.Boolean(string="Internal Transfer", readonly=False, tracking=True)
    destination_journal_id = fields.Many2one(comodel_name='account.journal',string='Destination Journal',domain="[('type', 'in', ('bank','cash')), ('id', '!=', journal_id)]",check_company=True,)

    @api.depends('payment_type', 'journal_id', 'currency_id','is_internal_transfer')
    def _compute_payment_method_line_fields(self):
        super()._compute_payment_method_line_fields()
        for pay in self:
            to_exclude = pay._get_payment_method_codes_to_exclude()
            if pay.is_internal_transfer:
                pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(pay.payment_type).filtered(
                    lambda x: x.code in ['manual'])

    # @api.depends('partner_id', 'journal_id', 'destination_journal_id')
    # def _compute_is_internal_transfer(self):
    #     for payment in self:
    #         payment.is_internal_transfer = payment.partner_id and payment.partner_id == payment.journal_id.company_id.partner_id and payment.destination_journal_id


    def action_open_destination_journal(self):
        self.ensure_one()

        action = {
            'name': _("Destination journal"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.journal',
            'context': {'create': False},
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.destination_journal_id.id,
        }
        return action
    
    def _get_aml_default_display_name_list(self):
        self.ensure_one()
        values = super()._get_aml_default_display_name_list()

        if self.is_internal_transfer:
            # Replace the label entry in the returned list
            for item in values:
                if item[0] == 'label':
                    item = ('label', _("Internal Transfer"))
                    break
            else:
                # If no 'label' was found, add one
                values.insert(0, ('label', _("Internal Transfer")))

            # Alternatively: force first item to be Internal Transfer label
            values[0] = ('label', _("Internal Transfer"))

        return values

    def _get_liquidity_aml_display_name_list(self):
        """ Hook allowing custom values when constructing the label to set on the liquidity line.

        :return: A list of terms to concatenate all together. E.g.
            [('reference', "INV/2018/0001")]
        """
        self.ensure_one()
        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                return [('transfer_to', _('Transfer to %s', self.journal_id.name))]
            else: # payment.payment_type == 'outbound':
                return [('transfer_from', _('Transfer from %s', self.journal_id.name))]
        elif self.payment_reference:
            return [('reference', self.payment_reference)]
        else:
            return self._get_aml_default_display_name_list()

    def _get_counterpart_aml_display_name_list(self):
        """ Hook allowing custom values when constructing the label to set on the counterpart line.

        :return: A list of terms to concatenate all together. E.g.
            [('reference', "INV/2018/0001")]
        """
        self.ensure_one()
        if self.payment_reference:
            return [('reference', self.payment_reference)]
        else:
            return self._get_aml_default_display_name_list()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :param force_balance: Optional balance.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or []

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %(payment_method)s payment method in the %(journal)s journal.",
                payment_method=self.payment_method_line_id.name, journal=self.journal_id.display_name))

        # Compute amounts.
        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
        write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        if not write_off_line_vals and force_balance is not None:
            sign = 1 if liquidity_amount_currency > 0 else -1
            liquidity_balance = sign * abs(force_balance)
        else:
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
        counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': counterpart_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        return line_vals_list + write_off_line_vals_list

    @api.depends('partner_id', 'company_id', 'payment_type', 'destination_journal_id', 'is_internal_transfer')
    def _compute_available_partner_bank_ids(self):
        for pay in self:
            if pay.payment_type == 'inbound':
                pay.available_partner_bank_ids = pay.journal_id.bank_account_id
            elif pay.is_internal_transfer:
                pay.available_partner_bank_ids = pay.destination_journal_id.bank_account_id
            else:
                pay.available_partner_bank_ids = pay.partner_id.bank_ids \
                    .filtered(lambda x: x.company_id.id in (False, pay.company_id.id))._origin

    @api.depends('is_internal_transfer')
    def _compute_partner_id(self):
        for pay in self:
            if pay.is_internal_transfer:
                pay.partner_id = pay.journal_id.company_id.partner_id
            elif pay.partner_id == pay.journal_id.company_id.partner_id:
                pay.partner_id = False
            else:
                pay.partner_id = pay.partner_id

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer', 'destination_journal_id')
    def _compute_destination_account_id(self):
        super()._compute_destination_account_id()

        for pay in self:
            if pay.is_internal_transfer and pay.destination_journal_id.company_id.transfer_account_id:
                pay.destination_account_id = pay.destination_journal_id.company_id.transfer_account_id

    @api.model
    def _get_trigger_fields_to_synchronize(self):
        # Get default fields from the parent
        fields = super()._get_trigger_fields_to_synchronize()

        # Add custom fields (e.g., 'is_internal_transfer') if not already present
        custom_fields = ('is_internal_transfer',)
        return tuple(set(fields + custom_fields))

    def _create_paired_internal_transfer_payment(self):
        ''' When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        '''
        for payment in self:
            paired_payment = payment.with_context(internal_transfer=True).copy({
                'journal_id': payment.destination_journal_id.id,
                'destination_journal_id': payment.journal_id.id,
                'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                'move_id': None,
                'payment_reference': payment.payment_reference,
                'paired_internal_transfer_payment_id': payment.id,
                'date': payment.date,
            })
            paired_payment._compute_payment_method_line_fields()
            # paired_payment.move_id._post(soft=False)
            # paired_payment.action_post()
            # payment.paired_internal_transfer_payment_id = paired_payment
            # body = _("This payment has been created from:") + payment._get_html_link()
            # paired_payment.message_post(body=body)
            # body = _("A second payment has been created:") + paired_payment._get_html_link()
            # payment.message_post(body=body)

            # lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
            #     lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
            # lines.reconcile()

    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''
        for pay in self:
            available_payment_method_lines = pay.available_payment_method_line_ids

            # Select the first available one by default.
            if pay.payment_method_line_id in available_payment_method_lines:
                pay.payment_method_line_id = pay.payment_method_line_id
            elif available_payment_method_lines:
                pay.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                pay.payment_method_line_id = False

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default)

        if 'internal_transfer' in self.env.context and self.env.context.get('internal_transfer'):
            for payment, vals in zip(self, vals_list):
                vals.update({
                    'journal_id': payment.destination_journal_id.id,
                })
                # Explicitly remove payment_method_line_id if present
                vals.pop('payment_method_line_id', None)

        return vals_list
    
    x_account_move_line_ids = fields.Many2many(comodel_name='account.move.line',string="Invoice Lines to Pay",help="Select invoice move lines (receivable/payable) that will be reconciled with this payment on posting.")
    write_off_line_ids = fields.One2many('account.payment.multiple',inverse_name='payment_id',string='Write-Off Lines',)
    total_write_off_line = fields.Monetary(string='Total Other', compute='_compute_amount_totals', compute_sudo=True,)
    total_all = fields.Monetary(string='Grand Total', compute='_compute_amount_totals', compute_sudo=True,)
    invoice_amount = fields.Monetary(string='Invoice Amount', compute='_compute_amount_invoice', compute_sudo=True,)
    x_manual_number = fields.Char(string='Number Manual')
    
    @api.depends('write_off_line_ids', 'amount')
    def _compute_amount_totals(self):
        for pay in self:
            debit = sum(pay.write_off_line_ids.mapped('debit'))
            credit = sum(pay.write_off_line_ids.mapped('credit'))

            adjustment = credit - debit

            pay.total_write_off_line = adjustment
            pay.total_all = adjustment + pay.amount
    
    @api.depends('x_account_move_line_ids')
    def _compute_amount_invoice(self):
        for pay in self:
            pay.invoice_amount = sum(pay.x_account_move_line_ids.mapped('amount_residual_currency'))

    def _prepare_move_line_default_vals_receive(self, write_off_line_vals=None):
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}
        line_vals_list = []

        # ================================
        # 1. WRITE-OFF LINES
        # ================================
        for line in self.write_off_line_ids:
            move_line_dict = {
                'account_id': line.account_id.id,
                'company_id': self.company_id.id,
                'currency_id': self.journal_id.currency_id.id or self.company_id.currency_id.id,
                'date_maturity': self.date,
                'name': line.name,
                'debit': line.debit,
                'credit': line.credit,
                'amount_currency': line.debit - line.credit
            }

            if line.analytic_account_id:
                move_line_dict['analytic_distribution'] = {line.analytic_account_id.id: 100}

            line_vals_list.append(move_line_dict)

        # ================================
        # 2. BANK LINE (Selalu Amount)
        # ================================
        bank_amount = self.amount if self.payment_type == 'inbound' else -self.amount

        bank_line = {
            'name': self.memo or self.name,
            'partner_id': self.partner_id.id,
            'account_id': self.outstanding_account_id.id,
            'date_maturity': self.date,
            'currency_id': self.currency_id.id,
            'amount_currency': bank_amount,
            'debit': bank_amount if bank_amount > 0 else 0.0,
            'credit': -bank_amount if bank_amount < 0 else 0.0,
        }

        line_vals_list.append(bank_line)

        # ================================
        # 3. PARTNER LINE (Balance otomatis)
        # ================================
        total_debit = sum(line['debit'] for line in line_vals_list)
        total_credit = sum(line['credit'] for line in line_vals_list)

        balance = total_debit - total_credit
        if balance != 0:
            partner_line = {
                'name': self.memo,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
                'date_maturity': self.date,
                'currency_id': self.currency_id.id,
                'amount_currency': -balance,
                'debit': -balance if balance < 0 else 0.0,
                'credit': balance if balance > 0 else 0.0,
            }
            line_vals_list.append(partner_line)

        return line_vals_list

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        for pay in self:
            if not pay.paired_internal_transfer_payment_id:
                return pay._prepare_move_line_default_vals_receive(write_off_line_vals)
            else:
                return super()._prepare_move_line_default_vals(write_off_line_vals, force_balance)

    @api.model
    def _get_trigger_fields_to_synchronize(self):
        return (
            'date', 'amount', 'payment_type', 'partner_type','payment_reference', 
            'paired_internal_transfer_payment_id','state', 'ref', 'currency_id', 
            'partner_id','destination_account_id','partner_bank_id', 'journal_id','write_off_line_ids', 'total_write_off_line'
        )

    def _synchronize_to_moves(self, changed_fields):
        for pay in self.with_context(skip_account_move_synchronization=True):

            if not pay.paired_internal_transfer_payment_id:

                if pay.state in ('draft', 'to_approve'):
                    if not any(name in changed_fields for name in self._get_trigger_fields_to_synchronize()):
                        return

                    if pay.move_id.state == 'posted':
                        pay.move_id.sudo().button_draft()

                    pay.move_id.line_ids.unlink()

                    line_ids_commands = [
                        (0, 0, vals)
                        for vals in pay._prepare_move_line_default_vals_receive()
                    ]

                    pay.move_id.with_context(skip_invoice_sync=True).write({
                        'journal_id': pay.journal_id.id,
                        'partner_id': pay.partner_id.id,
                        'currency_id': pay.currency_id.id,
                        'partner_bank_id': pay.partner_bank_id.id,
                        'date': pay.date,
                        'line_ids': line_ids_commands,
                    })

            else:
                return super(AccountPayment, self)._synchronize_to_moves(changed_fields)

    def action_post(self):
        for payment in self:
            if (payment.require_partner_bank_account and not payment.partner_bank_id.allow_out_payment):
                raise UserError(_(
                    "To record payments with %s, the recipient bank account must be manually validated. "
                    "You should go on the partner bank account of %s in order to validate it."
                ) % (payment.payment_method_line_id.name, payment.partner_id.display_name))

        # Call the super method to maintain standard behavior
        res = super().action_post()

        # Any custom logic after posting (if needed)
        self.filtered(lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id)._create_paired_internal_transfer_payment()
        for payment in self.sudo():
            if payment.x_account_move_line_ids and not payment.is_internal_transfer:
                # Ambil semua baris yang harus direkonsiliasi
                pay_move_line = payment.move_id.line_ids.filtered(
                    lambda l: l.account_id.id == payment.destination_account_id.id
                )
                x_move_line = payment.x_account_move_line_ids.filtered(
                    lambda l: l.account_id.id == payment.destination_account_id.id
                )
                line_all = (pay_move_line + x_move_line)

                lines = line_all.filtered(
                    lambda l: l.account_id == payment.destination_account_id and not l.reconciled
                )
                lines.reconcile()

        return res

    def action_draft(self):
        for pay in self:
            if pay.move_id.state == 'posted':
                pay.move_id.button_draft()
            if pay.move_id.state == 'draft':
                pay.move_id.button_cancel()
        return super().action_draft()