from odoo import fields, models, api, _


class QualityPoint(models.Model):
    _inherit = "quality.point"

    quantity = fields.Float('Quantity')
    type_form = fields.Selection([
        ('raw', 'Bahan Baku'),
        ('half', 'Setengah Jadi'),
        ('finish', 'Barang Jadi'),
        ('kemas', 'Bahan Kemasan')
    ], string="Jenis QC", default='raw')
    picking_number_id = fields.Many2one(string="Document Picking", comodel_name="stock.picking", domain="[('picking_type_id', 'in', picking_type_ids)]")
    master_data_id = fields.Many2one("form.data.qc", string="Master Data", domain="[('type_form', '=', type_form)]")
    # sample_location_ids = fields.Many2many("stock.location", string="Sample Locations")
    sample_location_id = fields.Many2one('stock.location', string="Sample Locations")
    tipe_pack = fields.Selection([
        ('sticker', 'Sticker'),('shrink', 'Shrink'),('dudukan', 'Dudukan'),
        ('part_ind_box', 'Partisi IND.Box'),('ind_box', 'Individual Box'),
        ('inner_box', 'Inner Box'),('master_box', 'Master Box'),
        ('cap', 'Cap Tutup'),('botol', 'Botol'),('pot', 'Pot'),
        ('cas_datar', 'Casing Datar'),('cas_lipstik', 'Casing Lipstik'),('cas_brush', 'Casing Brush'),
        ('pump', 'Pump'),('pum_shower', 'Pump Shower'),
        ('ring', 'Ring'),('tubset', 'Tubset'),
    ], string="Tipe Packaging")

    def action_see_data_qc(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("bmo_quality.action_data_qc_raw")
        action['domain'] = [('point_id', '=', self.id)]
        return action