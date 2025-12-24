import qrcode, base64
from io import BytesIO
from datetime import datetime
from odoo import fields, Command, models, api, _
from odoo.exceptions import ValidationError


class QualityCheck(models.Model):
    _inherit = "quality.check"
    _description = "Data QC"
    _rec_name = "no_document"

    no_document = fields.Char(string="Document No.", default="New", readonly=True)
    effective_date = fields.Date(string="Tanggal Berlaku", default=fields.Date.context_today)
    no_revision = fields.Char(string="No. Revisi")
    page = fields.Integer(string="Halaman")
    no_analysis = fields.Char(string="No. Analisa", default="New", readonly=True)
    examination_date = fields.Date(string="Tanggal Pemeriksaan", tracking=True)
    name_of_raw_material_id = fields.Many2one("product.product", string="Nama Bahan Baku")
    variants = fields.Char(string="Varian")
    production_date = fields.Date(string="Tanggal Produksi")
    production_capacity = fields.Float(string="Kapasitas Produksi")
    expired_date = fields.Datetime(string="Tanggal Kadaluarsa", related='lot_id.expiration_date', store=True)
    code_of_raw_material = fields.Char(string="Kode Bahan Baku", related='product_id.default_code')
    batch_no = fields.Char(string="No. Batch")
    supplier_or_customer_name_id = fields.Many2one('res.partner', string='Nama Supplier/customer')
    arrival_date = fields.Date(string="Tanggal Kedatangan")
    qty_received = fields.Float(string="Jumlah barang datang", compute="_comp_qty_receive")
    qty_fail = fields.Float("Qty Fail", tracking=True)
    qty_pass = fields.Float("Qty Pass", tracking=True)
    qty_of_items_sampled = fields.Float(string="Jumlah barang disampling")
    sampling_date = fields.Date(string="Tanggal Sampling")
    sampling_officer_id = fields.Many2one("res.users", string="Petugas Sampling", default=lambda self: self.env.user)
    sampling_officer = fields.Char(string="Petugas Sampling")
    qty_of_samples_per_date = fields.Float(string="Jumlah Sampel Pertinggal")
    data_qc_line = fields.One2many("quality.check.line", "data_qc_id", string="Data QC Lines")
    type_form = fields.Selection([
        ('raw', 'Bahan Baku'),
        ('half', 'Setengah Jadi'),
        ('finish', 'Barang Jadi'),
        ('kemas', 'Bahan Kemasan')
    ], string="Jenis QC")
    master_data_id = fields.Many2one("form.data.qc", string="Master Data", domain="[('type_form', '=', type_form)]")
    specific_gravity_line = fields.One2many("specific.gravity.line", "specific_gravity_id", string="Specific Gravity Lines")
    picno_weight_and_water = fields.Float(string="Berat Pikno + Air", digits=(16, 4), tracking=True)
    picno_weight = fields.Float(string="Berat Pikno + Kosong", digits=(16, 4), tracking=True)
    koh_volume = fields.Float(string="Volume KOH", compute="_compute_gravity_specific", digits=(16, 4), store=True )
    n_koh = fields.Float(string="N KOH", digits=(16, 4), tracking=True)
    mass_sample = fields.Float(string="Sample Massa", compute="_compute_gravity_specific", digits=(16, 4), store=True)
    gravity_specific = fields.Float(string="Berat Jenis", compute="_compute_gravity_specific", digits=(16, 4), store=True)
    acid = fields.Float(string="Bilangan Asam", compute="_compute_gravity_specific", digits=(16, 4), store=True)
    notes = fields.Text(string="Catatan")
    released = fields.Boolean(string="Released", compute="_comp_quality_state")
    hold = fields.Boolean(string="Hold", default=False)
    reject = fields.Boolean(string="Rejected", compute="_comp_quality_state")
    released_by_sortir = fields.Boolean(string="Released by Sortir")
    avg_specific_gravity = fields.Float(string="Rata-rata Specific Gravity", compute="_compute_avg_specific_gravity", store=True)
    # note = fields.Text(
    #     default="* Untuk Sediaan Serbuk\n** Untuk Sediaan Cream\n*** Untuk Sediaan Bibir atau sediaan yang mungkin untuk tertelan"
    # )
    quantity_per_batch = fields.Float(string="Jumlah Per Batch (pcs)")
    sampling_amount = fields.Float(string="Jumlah Sampling")
    audit_standards_line = fields.One2many("audit.standards.line", "audit_standards_line_id", string="Audit Standards Lines")
    analisa_pack_line = fields.One2many("analisa.packaging.line", "analisa_packaging_id", string="Analisa Package Lines")
    
    total_critical = fields.Float(compute="_compute_total", digits=(16, 1))
    total_major = fields.Float(compute="_compute_total", digits=(16, 1))
    total_minor = fields.Float(compute="_compute_total", digits=(16, 1))

    # AQL input manual
    aql_critical = fields.Float(digits=(16, 1))
    aql_major = fields.Float(digits=(16, 1))
    aql_minor = fields.Float(digits=(16, 1))
    persen_sampling = fields.Float('% Sampling', compute="_comp_persen_info", digits=(16, 2))
    persen_pass = fields.Float('% Pass', compute="_comp_persen_info", digits=(16, 2))
    persen_fail = fields.Float('% Fail', compute="_comp_persen_info", digits=(16, 2))

    @api.depends('qty_fail','qty_pass','qty_of_items_sampled','move_line_id.move_id')
    def _comp_persen_info(self):
        for rec in self:
            sml = self.env['stock.move.line'].search([('move_id','=',rec.move_line_id.move_id.id)])
            rec.persen_sampling = (rec.qty_of_items_sampled / sum(sml.mapped('quantity')))
            rec.persen_pass = (rec.qty_pass / sum(sml.mapped('quantity')))
            rec.persen_fail = (rec.qty_fail / sum(sml.mapped('quantity')))

    @api.depends("audit_standards_line.critical", "audit_standards_line.major", "audit_standards_line.minor")
    def _compute_total(self):
        for rec in self:
            rec.total_critical = sum(float(x) for x in rec.audit_standards_line.mapped("critical") if x)
            rec.total_major = sum(float(x) for x in rec.audit_standards_line.mapped("major") if x)
            rec.total_minor = sum(float(x) for x in rec.audit_standards_line.mapped("minor") if x)
    
    # Result
    result_critical = fields.Float(compute="_compute_result", digits=(16, 1))
    result_major = fields.Float(compute="_compute_result", digits=(16, 1))
    result_minor = fields.Float(compute="_compute_result", digits=(16, 1))

    @api.depends("total_critical", "total_major", "total_minor", "aql_critical", "aql_major", "aql_minor")
    def _compute_result(self):
        for rec in self:
            rec.result_critical = rec.total_critical - rec.aql_critical
            rec.result_major = rec.total_major - rec.aql_major
            rec.result_minor = rec.total_minor - rec.aql_minor

    total_defects = fields.Float(string="Total Defects")
    aql_allowed_defects = fields.Float(string="AQL Allowed Defects")
    aql_results	= fields.Float(string="AQL Results")
    point_id = fields.Many2one('quality.point', 'Control Point')
    # quality_state = fields.Selection(selection_add=[('sort', 'By Sortir')], ondelete={'view': 'cascade'})
    po_line_id = fields.Many2one('purchase.order.line', string='PO Line')
    tipe_pack = fields.Selection([
        ('sticker', 'Sticker'),('shrink', 'Shrink'),('dudukan', 'Dudukan'),
        ('part_ind_box', 'Partisi IND.Box'),('ind_box', 'Individual Box'),
        ('inner_box', 'Inner Box'),('master_box', 'Master Box'),
        ('cap', 'Cap Tutup'),('botol', 'Botol'),('pot', 'Pot'),
        ('cas_datar', 'Casing Datar'),('cas_lipstik', 'Casing Lipstik'),('cas_brush', 'Casing Brush'),
        ('pump', 'Pump'),('pum_shower', 'Pump Shower'),
        ('ring', 'Ring'),('tubset', 'Tubset'),
    ], string="Tipe Packaging")
    uom_datang = fields.Many2one('uom.uom', string="Uom Datang", related="move_line_id.move_id.product_uom")
    qr_url_link = fields.Binary("QR URL", compute="_compute_qr_url_link")

    show_picno_weight_and_water = fields.Boolean("Show Berat Pikno + Air", compute="_compute_data_show", store=True)
    show_picno_weight = fields.Boolean("Show Berat Pikno + Kosong", compute="_compute_data_show", store=True)
    show_koh_volume = fields.Boolean("Show Volume KOH", compute="_compute_data_show", store=True)
    show_n_koh = fields.Boolean("Show N KOH", compute="_compute_data_show", store=True)
    show_mass_sample = fields.Boolean("Show Sample Massa", compute="_compute_data_show", store=True)
    show_acid = fields.Boolean("Show Bilangan Asam", compute="_compute_data_show", store=True)
    show_gravity_specific = fields.Boolean(string="Show Berat Jenis", compute="_compute_data_show", store=True)

    @api.depends('specific_gravity_line.rincian_id')
    def _compute_data_show(self):
        for rec in self:
            lines = rec.specific_gravity_line.mapped('rincian_id')

            rec.show_picno_weight_and_water = any(lines.mapped('show_picno_weight_and_water'))
            rec.show_picno_weight = any(lines.mapped('show_picno_weight'))
            rec.show_koh_volume = any(lines.mapped('show_koh_volume'))
            rec.show_n_koh = any(lines.mapped('show_n_koh'))
            rec.show_mass_sample = any(lines.mapped('show_mass_sample'))
            rec.show_acid = any(lines.mapped('show_acid'))
            rec.show_gravity_specific = any(lines.mapped('show_gravity_specific'))



    def check_required_fields(self):
        for rec in self:
            if rec.type_form not in ['raw','half']:
                res_lines = rec.data_qc_line.mapped('result')
                if '' in res_lines or any(x == False or x == '' for x in res_lines):
                    raise ValidationError(_("Semua hasil pemeriksaan pada Data QC Lines harus diisi, Tidak Boleh Kosong."))
            # if rec.type_form == 'raw':
            #     check_field = [rec.picno_weight_and_water, rec.picno_weight, rec.n_koh]
                # if any(x == 0 for x in check_field):
                #     raise ValidationError(_("Berat Pikno + Air, Berat Pikno + Kosong, dan N KOH harus diisi dan tidak boleh 0."))
            if rec.type_form == 'semi':
                res_lines_average_results = rec.data_qc_line.mapped('average_results')
                if '' in res_lines_average_results or any(x == False or x == '' for x in res_lines_average_results):
                    raise ValidationError(_("Untuk QC Semi Finished, Hasil Analisa di Line harus diisi."))

    @api.depends('type_form')
    def _compute_qr_url_link(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            id_view = {
                'raw': 'bmo_quality.data_qc_form_raw',
                'kemas': 'bmo_quality.data_qc_form_kemas',
                'half': 'bmo_quality.semi_finished_raw_material_form',
                'finish': 'bmo_quality.finished_goods_form',
            }
            view = id_view[rec.type_form]
            # custom_view = self.env.ref(view, raise_if_not_found=False)
            # url = f"{base_url}/web#id={rec.id}&model={rec._name}&view_type=form&view_id={custom_view.id}"
            url = f"{base_url}/public/qc/{rec.id}?type={rec.type_form}"

            qr = qrcode.QRCode(version=1, box_size=3, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image()
            buf = BytesIO()
            img.save(buf, format="PNG")
            rec.qr_url_link = base64.b64encode(buf.getvalue())

    @api.depends('no_document')
    def _compute_display_name(self):
        for doc in self:
            name = doc.no_document or ''
            doc.display_name = name

    
    def _move_line_to_failure_location_sort(self):
        for check in self:
            qty = check.qty_fail +check.qty_pass + check.qty_of_items_sampled
            failure_location_id = self.point_id.failure_location_ids
            failed_qty = self.qty_failed
            move_line = check.move_line_id
            move = move_line.move_id
            move.picked = True
            dest_location = failure_location_id.id
            move_line.quantity = self.qty_pass
            failed_move_line = move_line.with_context(default_check_ids=None, no_checks=True).copy({
                'location_dest_id': dest_location,
                'quantity': self.qty_fail,
            })
            move.move_line_ids = [Command.link(failed_move_line.id)]
            dict_new_check = {
                'no_document': self.no_document,
                'no_analysis': self.no_analysis,
                'sampling_date': self.sampling_date,
                'sampling_officer': self.sampling_officer,
                'quality_state': 'fail',
                'user_id': self.env.user.id,
                'control_date': datetime.now(),
                'released_by_sortir': True,
                'move_line_id': move_line,
                'qty_tested': abs(self.qty_pass - self.qty_fail),
                'qty_of_items_sampled': self.qty_of_items_sampled,
                'qty_pass': 0,
                'qty_fail': self.qty_fail,
                'picno_weight_and_water': self.picno_weight_and_water,
                'picno_weight': self.picno_weight,
                'n_koh': self.n_koh,
                'aql_critical': self.aql_critical,
                'aql_major': self.aql_major,
                'aql_minor': self.aql_minor,
                'notes': self.notes,
            }
            check.move_line_id = failed_move_line
            check.qty_fail = 0
            new_check = self.create(failed_move_line._get_check_values(check.point_id))
            new_check.write(dict_new_check)
            new_check._onchange_master_data_qc()
            # if check.data_qc_line:
            #     new_check.data_qc_line = (6,0, check.data_qc_line.ids)
            # if check.specific_gravity_line:
            #     new_check.specific_gravity_line = (6,0, check.specific_gravity_line.ids)
            # if check.analisa_pack_line:
            #     new_check.analisa_pack_line = (6,0, check.analisa_pack_line.ids)
            # if check.audit_standards_line:
            #     new_check.audit_standards_line = (6,0, check.audit_standards_line.ids)
            # Copy One2many → One2many

            if check.data_qc_line:
                new_check.data_qc_line = False
                new_check.data_qc_line = [
                    (0, 0, line.copy_data()[0]) for line in check.data_qc_line
                ]

            if check.specific_gravity_line:
                new_check.specific_gravity_line = False
                new_check.specific_gravity_line = [
                    (0, 0, line.copy_data()[0]) for line in check.specific_gravity_line
                ]

            if check.analisa_pack_line:
                new_check.analisa_pack_line = False
                new_check.analisa_pack_line = [
                    (0, 0, line.copy_data()[0]) for line in check.analisa_pack_line
                ]

            if check.audit_standards_line:
                new_check.audit_standards_line = False
                new_check.audit_standards_line = [
                    (0, 0, line.copy_data()[0]) for line in check.audit_standards_line
                ]

    
    def _move_line_to_sample_location(self, sample_loc, sample_qty):
        for check in self:
            move_line = check.move_line_id
            move = move_line.move_id
            move.picked = True
            dest_location = sample_loc.id
            # move_line.quantity = move_line.quantity - sample_qty
            sample_move_line = move_line.with_context(default_check_ids=None, no_checks=True).copy({
                'location_dest_id': dest_location,
                'quantity': sample_qty,
            })
            move.move_line_ids = [Command.link(sample_move_line.id)]

    def do_by_sort(self):
        if self.qty_fail == 0 or self.qty_pass == 0:
            raise ValidationError(_("Untuk By Sortir, Qty Pass dan Qty Fail Tidak Boleh 0."))
        if self.qty_received != round(sum([self.qty_fail, self.qty_pass, self.qty_of_items_sampled]), 2):
            raise ValidationError(_("Tidak Bisa, Qty Tidak Sama dengan Qty Diterima."))
        self.check_required_fields()
        self._move_line_to_failure_location_sort()
        self.released_by_sortir = True
        if self.qty_of_items_sampled !=0:
            sample_dest = self.point_id.sample_location_id
            self._move_line_to_sample_location(sample_dest, self.qty_of_items_sampled)
        self.lot_id._compute_no_analisa_qc()
        self.write({'quality_state': 'pass',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
    
    def do_pass(self):
        if self.qty_fail > 0:
            raise ValidationError(_("Untuk Pass, Qty Fail Harus 0."))
        if self.qty_received != round(self.qty_pass + self.qty_of_items_sampled, 2):
            raise ValidationError(_("Tidak Bisa, Qty Pass Tidak Sama dengan Qty Diterima."))
        self.check_required_fields()
        data = super().do_pass()
        if self.qty_of_items_sampled !=0:
            self.move_line_id.quantity -= self.qty_of_items_sampled
            sample_dest = self.point_id.sample_location_id
            self._move_line_to_sample_location(sample_dest, self.qty_of_items_sampled)
        self.lot_id._compute_no_analisa_qc()
        return data   
    
    def do_fail(self):
        if self.qty_pass > 0:
            raise ValidationError(_("Untuk Fail, Qty Pass Harus 0."))
        if self.qty_received != round(self.qty_fail + self.qty_of_items_sampled, 2):
            raise ValidationError(_("Tidak Bisa, Qty Fail Tidak Sama dengan Qty Diterima."))
        self.check_required_fields()
        data = super().do_fail()
        fail_dest = self.point_id.failure_location_ids
        self._move_line_to_failure_location(fail_dest.id, self.qty_failed)
        if self.qty_of_items_sampled !=0:
            self.move_line_id.quantity -= self.qty_of_items_sampled
            sample_dest = self.point_id.sample_location_id
            self._move_line_to_sample_location(sample_dest, self.qty_of_items_sampled)
        self.lot_id._compute_no_analisa_qc()
        return data   

    @api.depends('quality_state')
    def _comp_quality_state(self):
        for qc in self:
            state = qc.quality_state
            qc.released = qc.reject = False
            if state == 'pass':
                qc.released = True
            if state == 'fail':
                qc.reject = True
            # if state == 'sort':
            #     qc.released_by_sortir = True

    @api.depends('move_line_id.move_id')
    def _comp_qty_receive(self):
        for qc in self:
            sml = self.env['stock.move.line'].search([('move_id','=',qc.move_line_id.move_id.id)])
            qc.qty_received = sum(sml.mapped('quantity'))
            # qc.qty_received = qc.move_line_id.quantity
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('no_document', 'New') == 'New' and vals.get('no_analysis', 'New') == 'New':
                seq_src = self.env['ir.sequence']
                today = datetime.today()
                # tanggal = today.strftime('%d-%m-%Y')
                # seq_number = self.env['ir.sequence'].next_by_code('data.qc')
                # seq_digits = seq_number[-4:] if seq_number else '0001'
                # vals['no_document'] = f"QC/{tanggal}/{seq_digits}"
                prods = self.env['product.product'].browse(vals.get('product_id'))
                lots = self.env['stock.lot'].browse(vals.get('lot_id'))
                # get number
                code_doc = code_analisa = ''
                if vals.get('type_form') == 'raw':
                    code_doc = 'data.qc.baku.doc'
                    code_analisa = 'data.qc.baku.analisa'
                elif vals.get('type_form') == 'kemas':
                    code_doc = 'data.qc.kemas.doc'
                    code_analisa = 'data.qc.kemas.analisa'
                elif vals.get('type_form') == 'half':
                    code_doc = 'data.qc.semi.doc'
                    code_analisa = 'data.qc.semi.analisa'
                elif vals.get('type_form') == 'finish':
                    code_doc = 'data.qc.finish.doc'
                    code_analisa = 'data.qc.finish.analisa'
                no_doc = seq_src.next_by_code(code_doc)
                no_analisa = seq_src.next_by_code(code_analisa)

                if vals.get('type_form') == 'raw':
                    no_doc = f'FRM/QC/RMT/{no_doc}'
                    no_analisa = f'B{today.strftime("%y")}{today.strftime("%m")}{no_analisa}'
                elif vals.get('type_form') == 'kemas':
                    no_doc = f'FRM/QC/PCK/{no_doc}'
                    no_analisa = f'K{today.strftime("%y")}{today.strftime("%m")}{no_analisa}'
                elif vals.get('type_form') == 'half':
                    no_doc = f'FRM//QC/BLK/{no_doc}'
                    no_analisa = f'QC/BLK/{prods.default_code}/{lots.name}/{no_analisa}'
                elif vals.get('type_form') == 'finish':
                    no_doc = f'FRM/QC/FPD/{prods.default_code}/{no_doc}'
                    no_analisa = f'QC/FDP/{prods.default_code}/{lots.name}/{no_analisa}'

                vals['no_document'] = no_doc
                vals['no_analysis'] = no_analisa

        return super().create(vals_list)


    @api.depends('specific_gravity_line.specific_gravity')
    def _compute_avg_specific_gravity(self):
        for record in self:
            values = record.specific_gravity_line.mapped('specific_gravity')
            record.avg_specific_gravity = sum(values) / len(values) if values else 0.0


    @api.depends('avg_specific_gravity', 'picno_weight', 'picno_weight_and_water', 'specific_gravity_line.value', 'n_koh')
    def _compute_gravity_specific(self):
        for record in self:
            k_vol = sample_mass = gravity = acid = 0
            lines = record.specific_gravity_line
            denominator = record.picno_weight_and_water - record.picno_weight
            if lines:
                berat_jenis = lines.filtered(lambda ln: ln.rincian_id.compute_type == 'berat_jenis')
                vol_koh = lines.filtered(lambda ln: ln.rincian_id.compute_type == 'vol_koh')
                sample = lines.filtered(lambda ln: ln.rincian_id.compute_type == 'sample')

                k_vol = sum(vol_koh.mapped('value'))
                sample_mass = sum(sample.mapped('value'))
                if k_vol != 0 and record.n_koh != 0:
                    acid = (k_vol * 56.1 * record.n_koh) / sample_mass
                if berat_jenis and denominator != 0:
                    gravity = (sum(berat_jenis.mapped('value')) - record.picno_weight) / denominator

            record.gravity_specific = gravity
            record.koh_volume = k_vol
            record.mass_sample = sample_mass
            record.acid = acid

    @api.onchange('master_data_id')
    def _onchange_master_data_qc(self):
        for rec in self:
            rec.data_qc_line = rec.specific_gravity_line = False
            if rec.master_data_id and rec.master_data_id.state == 'active' and rec.master_data_id.form_lines:
                lines = []
                for form_line in rec.master_data_id.form_lines:
                    lines.append((0, 0, {
                        'data_qc_id': rec.id,
                        'no_text': form_line.no_text,
                        'header_id': form_line.header_id.id,
                        'parameter': form_line.parameter,
                        'decimal_places' : form_line.decimal_places,
                        'standard': form_line.std,
                        'result': form_line.result,
                        'method': form_line.method,
                    }))
                rec.data_qc_line = lines
                rec.no_revision = rec.master_data_id.revision
                rec.no_document = f'{rec.no_document}-{rec.master_data_id.revision}'

                if rec.master_data_id.type_form == 'raw':
                    analisa_res = []
                    for analisa in rec.master_data_id.analisa_lines:
                        analisa_res.append((0, 0, {
                            'specific_gravity_id': rec.id,
                            'number': analisa.no_text,
                            'rincian_id': analisa.rincian_id.id,
                        }))
                    rec.specific_gravity_line = analisa_res


class QualityCheckLine(models.Model):
    _name = "quality.check.line"
    _description = "Data QC Line"

    data_qc_id = fields.Many2one("quality.check", string="Data QC",ondelete="cascade",)
    no_text = fields.Char('No.')
    header_id = fields.Many2one('data.header.line', string='Header')
    decimal_places = fields.Integer("Decimal Places", default="2")
    parameter = fields.Char(string="Parameter")
    standard = fields.Char(string="Standar")
    result = fields.Char(string="Hasil Pemeriksaan")
    method = fields.Char(string="Metode")
    top_results = fields.Char(string="Hasil Pemeriksaan Atas")
    mid_range_results = fields.Char(string="Hasil Pemeriksaan Tengah")
    bottom_results = fields.Char(string="Hasil Pemeriksaan Bawah")
    average_results = fields.Char(string="Hasil Analisa")

    @api.onchange('top_results', 'mid_range_results', 'bottom_results')
    def _onchange_avg(self):
        # Convert ke float kalau ada isinya, kalau kosong jadi 0
        vals = []
        for val in [self.top_results, self.mid_range_results, self.bottom_results]:
            try:
                vals.append(float(val))
            except (ValueError, TypeError):
                vals.append(0)

        non_zero = [v for v in vals if v != 0]

        if non_zero:
            avg = round(sum(non_zero) / len(non_zero), self.decimal_places)
            self.average_results = str(avg)

class SpecificGravityLine(models.Model):
    _name = "specific.gravity.line"
    _description = "Specific Gravity Line"

    specific_gravity_id = fields.Many2one("quality.check", string="Data QC",ondelete="cascade",)
    specific_gravity = fields.Float(string="Berat Jenis + Sampel")
    ph = fields.Float(string="pH")
    melting_point = fields.Float(string="Titik Leleh")
    viscosity = fields.Float(string="Viscosity")
    sample_mass = fields.Float(string="Bil. Sample Mass")
    volume_koh = fields.Float(string="Bil. Volume KOH")
    rincian_id = fields.Many2one("rincian.analisa", string="Rincian Analisa")
    rincian_code = fields.Char(related="rincian_id.code", string="Code", store=True)
    number = fields.Char('No.')
    n_1 = fields.Float(string="1", digits=(16, 4))
    n_2 = fields.Float(string="2", digits=(16, 4))
    n_3 = fields.Float(string="3", digits=(16, 4))
    n_4 = fields.Float(string="4", digits=(16, 4))
    n_5 = fields.Float(string="5", digits=(16, 4))
    n_6 = fields.Float(string="6", digits=(16, 4))
    n_7 = fields.Float(string="7", digits=(16, 4))
    n_8 = fields.Float(string="8", digits=(16, 4))
    n_9 = fields.Float(string="9", digits=(16, 4))
    n_10 = fields.Float(string="10", digits=(16, 4))
    value = fields.Float(string="AVG", compute="_compute_value", digits=(16, 4), store=True)
    
    @api.depends('n_1','n_2','n_3','n_4','n_5','n_6','n_7','n_8','n_9','n_10')
    def _compute_value(self):
        for k in self:
            k.value = 0.0
            nums = [k.n_1, k.n_2, k.n_3, k.n_4, k.n_5, k.n_6, k.n_7, k.n_8, k.n_9, k.n_10]
            valid_nums = [num for num in nums if num > 0]
            if valid_nums:
                k.value = sum(valid_nums) / len(valid_nums)    

class AnalisaPackagingLine(models.Model):
    _name = "analisa.packaging.line"
    _description = "Analisa Kemasan Line"

    analisa_packaging_id = fields.Many2one("quality.check", string="Data QC")
    tipe_pack = fields.Selection([
        ('sticker', 'Sticker'),('shrink', 'Shrink'),('dudukan', 'Dudukan'),
        ('part_ind_box', 'Partisi IND.Box'),('ind_box', 'Individual Box'),
        ('inner_box', 'Inner Box'),('master_box', 'Master Box'),
        ('cap', 'Cap Tutup'),('botol', 'Botol'),('pot', 'Pot'),
        ('cas_datar', 'Casing Datar'),('cas_lipstik', 'Casing Lipstik'),('cas_brush', 'Casing Brush'),
        ('pump', 'Pump'),('pum_shower', 'Pump Shower'),
        ('ring', 'Ring'),('tubset', 'Tubset'),
    ], string="Tipe Packaging", related="analisa_packaging_id.tipe_pack", store=True)

    front_long = fields.Float("Panjang Depan")
    front_wide = fields.Float("Lebar Depan")
    front_heigh = fields.Float("Tinggi Depan")

    back_long = fields.Float("Panjang Belakang")
    back_wide = fields.Float("Lebar Belakang")
    back_heigh = fields.Float("Tinggi Belakang")

    cap = fields.Float("Tutup")
    cap_heigh = fields.Float("Tinggi Tutup")
    cap_deep = fields.Float("Dalam Tutup")

    weight = fields.Float("Bobot")
    weight_tube_set = fields.Float("Bobot Tube Set")

    heigh_bottle = fields.Float("Tinggi Botol")
    heigh_neck = fields.Float("Tinggi Leher")
    heigh_pump = fields.Float("Tinggi Pump")
    heigh_ring = fields.Float("Tinggi Ring")
    heigh_tube_set = fields.Float("Tinggi Tube Set")
    heigh_outside = fields.Float("Tinggi Luar")
    heigh_neck_plug = fields.Float("Tinggi Leher + Plug")

    long_hose = fields.Float("Panjang Selang")
    long_pump = fields.Float("Panjang Pump Tanpa Selang")
    long_noozle = fields.Float("Panjang Noozel")

    long = fields.Float("Panjang")
    wide = fields.Float("Lebar")
    heigh = fields.Float("Tinggi")
    thick = fields.Float("Tebal")
    hole = fields.Float("Lubang")
    thread = fields.Float("Ulir/Snap")
    weight = fields.Float("Bobot")
    
    cas_thread = fields.Float("Casing Ulir/Snap")
    cas_mounth = fields.Float("Casing Mulut")

    vol_brimfull = fields.Float("Volume Brimfull")
    mounth = fields.Float("Mulut")
    outside = fields.Float("Luar")
    deep = fields.Float("Dalam")
    plug = fields.Float("Plug")
    hose = fields.Float("Selang")  
    tube = fields.Float("Tube")


class AuditStandardsLine(models.Model):
    _name = "audit.standards.line"
    _description = "Audit Standards Line"

    audit_standards_line_id = fields.Many2one("quality.check", string="Data QC",ondelete="cascade",)
    defect_description = fields.Char(string="Defect Description")
    critical = fields.Float(string="Critical (0,65)", digits=(16, 1))
    major = fields.Float(string="Major (2,5)", digits=(16, 1))
    minor = fields.Float(string="Minor (6,5)", digits=(16, 1))