from collections import defaultdict
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def check_quality(self):
        if all(not move.picked for move in self.move_ids):
            checkable_lines = self.move_line_ids
        else:
            checkable_lines = self.move_line_ids.filtered(
            lambda ml: (
                ml.move_id.picked and
                not float_is_zero(ml.quantity, precision_rounding=ml.product_uom_id.rounding)
            ))
        checkable_products = checkable_lines.product_id
        checks = self.check_ids.filtered(lambda check: check.quality_state == 'none' and (check.product_id in checkable_products or check.measure_on == 'operation'))
        if checks:
            raise ValidationError(
				_('QC Belum Selesai.'))
            # return checks.action_open_quality_check_wizard()
        return False

    def action_open_quality_check_picking(self):
        qc = self.check_ids
        views = "quality_control.quality_check_action_picking"

        if qc[0].type_form == 'raw':
            views = "bmo_quality.action_data_qc_raw"
        elif qc[0].type_form == 'half':
            views = "bmo_quality.action_data_qc_half"
        elif qc[0].type_form == 'finish':
            views = "bmo_quality.action_finished_goods"
        elif qc[0].type_form == 'kemas':
            views = "bmo_quality.action_data_qc_kemas"

        action = self.env["ir.actions.actions"]._for_xml_id(views)
        action['context'] = self.env.context.copy()
        action['context'].update({
            'search_default_picking_id': [self.id],
            'default_picking_id': self.id,
            'show_lots_text': self.show_lots_text,
        })
        return action
    
class StockMove(models.Model):
    _inherit = "stock.move"

    check_ids = fields.Many2many('quality.check', string='Checks', compute='_compute_check_ids')
    no_analisa_qc = fields.Char(string='No. Analisa QC', compute='_compute_no_analisa_qc')

    @api.depends("lot_ids")
    def _compute_no_analisa_qc(self):
        for sm in self:
            no_list = ''
            if sm.lot_ids:
                no_list = [n.no_analisa_qc.strip() for n in sm.lot_ids if n.no_analisa_qc and n.no_analisa_qc.strip()]
            sm.no_analisa_qc = '' if not no_list else ', '.join(no_list)

    @api.depends("move_line_ids.check_ids")
    def _compute_check_ids(self):
        for move in self:
            if move.move_line_ids:
                move.check_ids = move.move_line_ids.mapped("check_ids")
            else:
                move.check_ids = False
    
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    no_analisa_qc = fields.Char(string='No. Analisa QC', related='lot_id.no_analisa_qc')

    def _create_check(self):
        check_values_list = []
        quality_points_domain = self.env['quality.point']._get_domain(
            self.product_id, self.move_id.picking_type_id, measure_on='move_line')
        quality_points = self.env['quality.point'].sudo().search(quality_points_domain)
        quality_points_by_product_picking_type = {}
        for quality_point in quality_points:
            for product in quality_point.product_ids:
                for picking_type in quality_point.picking_type_ids:
                    quality_points_by_product_picking_type.setdefault(
                        (product, picking_type), set()).add(quality_point.id)
            for categ in quality_point.product_category_ids:
                categ_product = self.env['product.product'].search([
                    ('categ_id', 'child_of', categ.id)
                ])
                for product in categ_product & self.product_id:
                    for picking_type in quality_point.picking_type_ids:
                        quality_points_by_product_picking_type.setdefault(
                            (product, picking_type), set()).add(quality_point.id)
            if not quality_point.product_ids and not quality_point.product_category_ids:
                for picking_type in quality_point.picking_type_ids:
                    quality_points_by_product_picking_type.setdefault(
                        (None, picking_type), set()).add(quality_point.id)

        for ml in self:
            quality_points_product = quality_points_by_product_picking_type.get((ml.product_id, ml.move_id.picking_type_id), set())
            quality_points_all_products = ml._get_quality_points_all_products(quality_points_by_product_picking_type)
            quality_points = self.env['quality.point'].sudo().search([('id', 'in', list(quality_points_product | quality_points_all_products))])
            for quality_point in quality_points:
                if quality_point.check_execute_now():
                    check_values = ml._get_check_values(quality_point)
                    check_values_list.append(check_values)
        if check_values_list:
            qc = self.env['quality.check'].sudo().create(check_values_list)
            qc._onchange_master_data_qc()

    def _get_check_values(self, quality_point):
        data = super()._get_check_values(quality_point)
        if not quality_point.master_data_id:
            raise ValidationError(_("Master Data Kosong."))
        data['qty_received'] = self.quantity
        data['type_form'] = quality_point.type_form
        data['master_data_id'] = quality_point.master_data_id.id
        data['qty_of_items_sampled'] = 0
        data['po_line_id'] = False if not self.move_id.po_line_id else self.move_id.po_line_id.id
        data['examination_date'] = datetime.today()
        data['arrival_date'] = datetime.today()
        data['production_date'] = datetime.today()
        data['supplier_or_customer_name_id'] = self.move_id.po_line_id.order_id.partner_id.id
        data['tipe_pack'] = quality_point.tipe_pack

        return data