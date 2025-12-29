from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import get_lang
from datetime import datetime
import pytz


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    request_id = fields.Many2one(
        comodel_name="purchase.request", string="Purchase Request", store=True)
    p_categ = fields.Selection([
        ('bahan_baku', 'Bahan Baku'),('bahan_kemas', 'Bahan Kemas'),
        ('lain', 'Lain Lain'),
        ], string='Purchase Category')

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin, pr_id):
        data = super(PurchaseRequestLineMakePurchaseOrder, self)._prepare_purchase_order(picking_type, group_id, company, origin)
        # pr_id = self.item_ids[0].request_id
        
        data['types'] = pr_id.types
        data['p_categ'] = self.p_categ
        data['from_pr'] = True
        data['origin'] = self.request_id.name
        return data
    
    @api.model
    def _prepare_item(self, line):
        val = line.product_qty - line.purchased_qty
        if line.product_qty > line.purchased_qty:
            return {
                "line_id": line.id,
                "request_id": line.request_id.id,
                "product_id": line.product_id.id,
                "name": line.name or line.product_id.name,
                "product_qty": val if val > 0 else line.pending_qty_to_receive,
                "product_uom_id": line.product_uom_id.id,
            }
    
    @api.model
    def get_items(self, request_line_ids):
        request_line_obj = self.env["purchase.request.line"]
        po_line_obj = self.env['purchase.order.line']

        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        self._check_valid_request_line(request_line_ids)
        self.check_group(request_lines)
        for line in request_lines:
            if not line.purchased_qty >= line.product_qty:
                items.append([0, 0, self._prepare_item(line)])
        return items
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model", False)
        request_line_ids = []
        pr_id = False
        if active_model == "purchase.request.line":
            request_line_ids += self.env.context.get("active_ids", [])
            pr_line = self.env['purchase.request.line'].browse(request_line_ids)
            print(request_line_ids,'sssssssss')
        elif active_model == "purchase.request":
            pr_id = self.env.context.get('active_id')
            request_ids = self.env.context.get("active_ids", False)
            request_line_ids += (
                self.env[active_model].browse(request_ids).mapped("line_ids.id")
            )
        if not request_line_ids:
            return res
        res["item_ids"] = self.get_items(request_line_ids)
        request_lines = self.env["purchase.request.line"].browse(request_line_ids)
        supplier_ids = request_lines.mapped("supplier_id").ids
        res["request_id"] = pr_id
        return res
    
    def make_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]
        pr_line_obj = self.env["purchase.request.line"]
        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        purchase = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise UserError(_("Enter a positive quantity."))
            if self.purchase_order_id:
                purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(
                    line.request_id.picking_type_id,
                    line.request_id.group_id,
                    line.company_id,
                    line.origin,
                    line.request_id,
                )
                purchase = purchase_obj.create(po_data)

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True
            # If Unit of Measure is not set, update from wizard.
            if not line.product_uom_id:
                line.product_uom_id = item.product_uom_id
            # Allocation UoM has to be the same as PR line UoM
            alloc_uom = line.product_uom_id
            wizard_uom = item.product_uom_id
            if available_po_lines and not item.keep_description:
                new_pr_line = False
                po_line = available_po_lines[0]
                po_line.purchase_request_lines = [(4, line.id)]
                po_line.move_dest_ids |= line.move_dest_ids
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            else:
                po_line_data = self._prepare_purchase_order_line(purchase, item)
                if item.keep_description:
                    po_line_data["name"] = item.name
                po_line = po_line_obj.create(po_line_data)
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            # TODO: Check propagate_uom compatibility:
            new_qty = pr_line_obj._calc_new_qty(
                line, po_line=po_line, new_pr_line=new_pr_line
            )
            po_line.product_qty = new_qty
            # The quantity update triggers a compute method that alters the
            # unit price (which is what we want, to honor graduate pricing)
            # but also the scheduled date which is what we don't want.
            date_required = item.line_id.date_required
            # we enforce to save the datetime value in the current tz of the user
            po_line.date_planned = (
                user_tz.localize(
                    datetime(date_required.year, date_required.month, date_required.day)
                )
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            res.append(purchase.id)
        purchase._onchange_for_picking_type()
        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "list,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }