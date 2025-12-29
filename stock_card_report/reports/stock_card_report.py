# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pytz

from odoo import api, fields, models


class StockCardView(models.TransientModel):
    _name = "stock.card.view"
    _description = "Stock Card View"
    _order = "date asc, id_data asc"

    date = fields.Datetime()
    id_data = fields.Integer(string='Id Data')
    product_id = fields.Many2one(comodel_name="product.product")
    partner_id = fields.Many2one('res.partner')
    product_qty = fields.Float()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one(comodel_name="uom.uom")
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name="stock.location")
    location_dest_id = fields.Many2one(comodel_name="stock.location")
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    picking_id = fields.Many2one(comodel_name="stock.picking")
    display_name = fields.Char("Name", compute="_compute_display_name", store=True)

    @api.depends("reference", "picking_id")
    def _compute_display_name(self):
        for rec in self:
            name = rec.reference
            if rec.picking_id.origin:
                name = "{} ({})".format(name, rec.picking_id.origin)
            rec.display_name = name

class StockCardReport(models.TransientModel):
    _name = "report.stock.card.report"
    _description = "Stock Card Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")
    location_id = fields.Many2one(comodel_name="stock.location")
    company_id = fields.Many2one(comodel_name="res.company")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="stock.card.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        locations = self.location_id 
        # self.env["stock.location"].search(
        #     [("id", "child_of", [self.location_id.id])]
        # )
        self._cr.execute(
            """
            SELECT 
                move_line.id AS id_data,
                move_line.date, 
                move_line.product_id, 
                move.partner_id,
                move.product_qty,
                move.product_uom_qty, 
                move.product_uom, 
                move_line.reference,
                move_line.location_id, 
                move_line.location_dest_id,
                case when move_line.location_dest_id in %s
                    then move_line.quantity end as product_in,
                case when move_line.location_id in %s
                    then move_line.quantity end as product_out,
                case when move_line.date < %s then True else False end as is_initial,
                move.picking_id
            FROM stock_move_line move_line
            LEFT JOIN stock_move move on(move.id = move_line.move_id)
            WHERE (move_line.location_id in %s or move_line.location_dest_id in %s)
                and move_line.state = 'done' and move_line.product_id in %s
                and CAST(move_line.date AS date) <= %s and move_line.company_id = %s
            ORDER BY move_line.date asc
        """,
            # ORDER BY move_line.date, move_line.id
            (
                tuple(locations.ids),
                tuple(locations.ids),
                date_from,
                tuple(locations.ids),
                tuple(locations.ids),
                tuple(self.product_ids.ids),
                self.date_to,
                self.company_id.id,
            ),
        )
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env["stock.card.view"]
        self.results = [ReportLine.new(line).id for line in stock_card_results]
    
    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        return product_input_qty - product_output_qty

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("stock_card_report.action_stock_card_report_xlsx")
            or self.env.ref("stock_card_report.action_stock_card_report_pdf")
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env["ir.qweb"]._render(
                "stock_card_report.report_stock_card_report_html", rcontext
            )
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**(given_context or {}))._get_html()
