# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class InventoryLineValue(models.Model):
    _name = "stock.inventory.line.value"
    _description = "Inventory Adjustments Line Value"
    _order = "product_id, inventory_id"

    inventory_id = fields.Many2one(
        'stock.inventory', 'Inventory', index=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product', domain=[('type', '=', 'product')], index=True, required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure', required=True)
    product_uom_category_id = fields.Many2one(string='Uom category', related='product_uom_id.category_id', readonly=True)
    product_qty = fields.Float(
        'Checked Quantity',
        digits='Product Unit of Measure', default=0)
    # lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number', domain="[('product_id', '=', product_id)]")
    # lot_name = fields.Char(string='Lot/Serial Name', help="Fill this if you want to create a new Serial/Lot number.")
    company_id = fields.Many2one(
        'res.company', 'Company', related='inventory_id.company_id', index=True, readonly=True, store=True)
    # state = fields.Selection(
    #     related='inventory_id.state', string='Status')
    theoretical_qty = fields.Float(
        'Theoretical Quantity', compute='_compute_theoretical_qty',
        digits='Product Unit of Measure', store=True)
    # inventory_location_id = fields.Many2one(
    #     'stock.location', 'Inventory Location', related='inventory_id.location_id', related_sudo=False, readonly=False)
    old_value = fields.Float(
        'Old Value', compute='_compute_theoretical_qty', readonly=True, store=True)
    value_new = fields.Float(string='New Value')
    value_diff = fields.Float(string='Vlaue Diff', compute='_compute_diff', store=True)
    price_unit_new = fields.Float(string='Price Unit', compute='_compute_price_unit')
    
    @api.depends('theoretical_qty','value_new','old_value')
    def _compute_price_unit(self):
        for line in self:
            if line.theoretical_qty > 0 and line.value_new > 0:
                price_unit = line.value_new / line.theoretical_qty
            else:
                price_unit = 0
            line.price_unit_new = price_unit
    
    @api.depends('value_new','old_value')
    def _compute_diff(self):
        for line in self:
            line.value_diff = line.value_new - line.old_value

    @api.depends('product_id', 'product_uom_id', 'company_id')
    def _compute_theoretical_qty(self):
        for line in self:
            if not line.product_id:
                line.old_value = 0
                line.theoretical_qty = 0
                continue
            value_product = line.product_id
            line.old_value = value_product.value_svl
            line.theoretical_qty = value_product.qty_available

    # @api.onchange('product_id')
    # def _onchange_product(self):
    #     res = {}
    #     if self.product_id:
    #         self.product_uom_id = self.product_id.uom_id
    #     return res

    # @api.onchange('product_id', 'location_id', 'product_uom_id')
    # def _onchange_quantity_context(self):
    #     if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
    #         self._compute_theoretical_qty()
    #         self.product_qty = self.theoretical_qty
    #         self.value_new = self.old_value

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for values in vals_list:
    #         if 'product_id' in values and 'product_uom_id' not in values:
    #             values['product_uom_id'] = self.env['product.product'].browse(values['product_id']).uom_id.id
    #     res = super(InventoryLine, self).create(vals_list)
    #     res._check_no_duplicate_line()
    #     return res


    # def write(self, vals):
    #     res = super(InventoryLine, self).write(vals)
    #     self._check_no_duplicate_line()
    #     return res

    # def _check_no_duplicate_line(self):
    #     for line in self:
    #         existings = line.search([
    #             ('id', '!=', line.id),
    #             ('product_id', '=', line.product_id.id),
    #             ('inventory_id', '=', line.inventory_id.id),
    #         ])
    #         if existings:
    #             raise UserError(_(f'You cannot have two inventory adjustments  with the same product {line.product_id.display_name}'))
    
    # @api.constrains('product_id')
    # def _check_product_id(self):
    #     for line in self:
    #         if line.product_id.type != 'consu':
    #             raise ValidationError(_("You can only adjust storable products.") + '\n\n%s -> %s' % (line.product_id.display_name, line.product_id.type))

    # def _get_move_values(self, qty, location_id, location_dest_id, out):
    #     self.ensure_one()
    #     return {
    #         'name': _('INV:') + (self.inventory_id.name or ''),
    #         'product_id': self.product_id.id,
    #         'product_uom': self.product_uom_id.id,
    #         'product_uom_qty': qty,
    #         'date': self.inventory_id.date,
    #         'company_id': self.company_id.id or self.env.company.id,
    #         'x_inventory_id': self.inventory_id.id,
    #         'x_inventory_line_id': self.id,
    #         'state': 'confirmed',
    #         'location_id': location_id,
    #         'location_dest_id': location_dest_id,
    #         'is_inventory': True,
    #         'picked': True,
    #         'move_line_ids': [(0, 0, {
    #             'product_id': self.product_id.id,
    #             'product_uom_id': self.product_uom_id.id,
    #             'qty_done': qty,
    #             'location_id': location_id,
    #             'location_dest_id': location_dest_id,
    #             'company_id': self.company_id.id or self.env.company.id,
    #             'x_inventory_id': self.inventory_id.id,
    #             'lot_id': self.lot_id.id if self.lot_id else False,
    #             'lot_name': self.lot_name if not self.lot_id else False,
    #         })]
    #     }

    # @api.constrains('product_id', 'lot_id', 'lot_name')
    # def _check_lot_required(self):
    #     for line in self:
    #         if line.product_id.tracking != 'none' and not (line.lot_id or line.lot_name):
    #             raise ValidationError(_("Product %s requires a Lot/Serial number.") % line.product_id.display_name)
    
    # def _generate_moves(self):
    #     vals_list = []
    #     for line in self:
    #         if line.inventory_id.type_adjustments != 'value_only':
    #             if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
    #                 continue
    #             diff = line.theoretical_qty - line.product_qty
    #             if diff < 0:  # found more than expected
    #                 vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
    #             else:
    #                 vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
    #             vals_list.append(vals)
    #     return self.env['stock.move'].create(vals_list)

    # def action_validate_revaluation(self):
    #     self.ensure_one()
    #     if self.inventory_id.type_adjustments == 'value_only' and self.value_diff != 0:
    #         product_id = self.product_id.with_company(self.company_id)
    #         description = _('INV:') + (self.inventory_id.name or '')

    #         revaluation_svl_vals = {
    #             'company_id'    : self.company_id.id,
    #             'x_inventory_id': self.inventory_id.id,
    #             'product_id'    : product_id.id,
    #             'reference'     : description,
    #             'description'   : description,
    #             'value'         : self.value_diff,
    #             'quantity'      : 0,
    #         }
    #         revaluation_svl = self.env['stock.valuation.layer'].create(revaluation_svl_vals)

    #         accounts = product_id.product_tmpl_id.get_product_accounts()
    #         debit_account_id = False
    #         credit_account_id = False

    #         if self.value_diff < 0:
    #             debit_account_id = product_id.property_stock_inventory.valuation_out_account_id.id if product_id.property_stock_inventory.valuation_out_account_id else accounts.get('stock_output') and accounts['stock_output'].id
    #             credit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id
    #         else:
    #             debit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id
    #             credit_account_id = product_id.property_stock_inventory.valuation_in_account_id.id if product_id.property_stock_inventory.valuation_in_account_id else accounts.get('stock_input') and accounts['stock_input'].id

    #         move_vals = {
    #             'journal_id'    : accounts['stock_journal'].id,
    #             'company_id'    : self.company_id.id,
    #             'ref'           : _("Revaluation of %s", product_id.display_name),
    #             'date'          : self.inventory_id.date,
    #             'stock_valuation_layer_ids': [(6, None, [revaluation_svl.id])],
    #             'move_type' : 'entry',
    #             'line_ids'  : [(0, 0, {
    #                 'name'      : description,
    #                 'account_id': debit_account_id,
    #                 'debit'     : abs(self.value_diff),
    #                 'credit'    : 0,
    #                 'product_id': product_id.id,
    #             }), (0, 0, {
    #                 'name'      : description,
    #                 'account_id': credit_account_id,
    #                 'debit'     : 0,
    #                 'credit'    : abs(self.value_diff),
    #                 'product_id': product_id.id,
    #             })],
    #         }
    #         account_move = self.env['account.move'].create(move_vals)
    #         account_move._post()

    #     return True