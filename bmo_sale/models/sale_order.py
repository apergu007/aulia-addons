from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_type = fields.Selection([
        ('reguler', 'Reqular'),('maklon', 'Maklon'),
        ('sample', 'Sample')], string='Sales Type')
    saldo_sisa = fields.Monetary('Sisa Saldo', related="partner_id.saldo_sisa")
    sale_categ_id = fields.Many2one('sales.category', 'Sales Category')
    sale_order_template_ids = fields.Many2many(
        comodel_name='sale.order.template',
        string="Quotation Template",
        store=True, readonly=False, check_company=True, precompute=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    po_number = fields.Char('PO Number')
    employee_id = fields.Many2one('hr.employee', 'Salesperson',compute='_compute_user_id',
        store=True, readonly=False, precompute=True, index=True,)
    
    @api.depends('partner_id')
    def _compute_user_id(self):
        res = super(SaleOrder, self)._compute_user_id()
        for order in self:
            order.employee_id = False
            if order.partner_id.employee_id:
                order.employee_id = order.partner_id.employee_id.id
        return res
    
    @api.onchange('sale_order_template_ids')
    def _onchange_sale_order_template_ids(self):
        if not self.sale_order_template_ids:
            return

        sale_order_template_ids = self.sale_order_template_ids.with_context(lang=self.partner_id.lang)
        order_lines_data = [fields.Command.clear()]
        for lines in sale_order_template_ids:
            order_lines_data += [
                fields.Command.create(line._prepare_order_line_values())
                for line in lines.sale_order_template_line_ids
            ]
        self.order_line = order_lines_data

    def action_confirm(self):
        if self.partner_id.saldo_active:
            if self.partner_id.saldo_sisa < self.amount_total:
                if not self.env.user.has_group('bmo_sale.group_sale_approve_saldo_limit'):
                    raise UserError(_(f'Tidak Bisa Transaksi, \n Sisa Saldo {self.partner_id.saldo_sisa}'))
        if not self.env.user.has_group('bmo_sale.group_sale_button_confirm'):
            raise UserError(_(f'Tidak Punya Approval Confirm'))
        return super(SaleOrder, self).action_confirm()
    
    @api.onchange('sale_type')
    def _onchange_sale_type(self):
        for k in self:
            if k.sale_type:
                sale_team_src = self.env['approval.sales.team'].search([('sale_type','=',k.sale_type)])
                if sale_team_src:
                    if len(sale_team_src)>1:
                        raise UserError(_(f'Approval Team Lebih Dari 1 Dengan type {k.sale_type}'))
                    k.sale_team_id = sale_team_src.id

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'

#     @api.depends('product_id', 'product_uom', 'product_uom_qty','order_id.sale_type')
#     def _compute_price_unit(self):
#         for line in self:
#             # Don't compute the price for deleted lines.
#             if not line.order_id:
#                 continue
#             # check if the price has been manually set or there is already invoiced amount.
#             # if so, the price shouldn't change as it might have been manually edited.
#             if (
#                 (line.technical_price_unit != line.price_unit and not line.env.context.get('force_price_recomputation'))
#                 or line.qty_invoiced > 0
#                 or (line.product_id.expense_policy == 'cost' and line.is_expense)
#             ):
#                 continue
#             line = line.with_context(sale_write_from_compute=True)
#             if not line.product_uom or not line.product_id:
#                 line.price_unit = 0.0
#                 line.technical_price_unit = 0.0
#             else:
#                 line = line.with_company(line.company_id)
#                 price = line._get_display_price()
#                 pricess = line.product_id._get_tax_included_unit_price_from_price(
#                     price,
#                     product_taxes=line.product_id.taxes_id.filtered(
#                         lambda tax: tax.company_id == line.env.company
#                     ),
#                     fiscal_position=line.order_id.fiscal_position_id,
#                 )
#                 if line.order_id.sale_type == 'sample':
#                     pricess = 0
#                 line.price_unit = pricess
#                 line.technical_price_unit = line.price_unit