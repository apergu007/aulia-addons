from odoo import fields, models, api, _

class RincianAnalisa(models.Model):
    _name = "rincian.analisa"
    _description = "Rincian Analisa"

    name = fields.Char('Name')
    code = fields.Char('Code')
    compute_type = fields.Selection([
        ('berat_jenis', 'Berat Jenis'),('vol_koh', 'Volume KOH'),
        ('sample', 'Sample Massa')
        ], string='Compute type')
    
    show_picno_weight_and_water = fields.Boolean("Show Berat Pikno + Air")
    show_picno_weight = fields.Boolean("Show Berat Pikno + Kosong")
    show_koh_volume = fields.Boolean("Show Volume KOH")
    show_n_koh = fields.Boolean("Show N KOH")
    show_mass_sample = fields.Boolean("Show Sample Massa")
    show_acid = fields.Boolean("Show Bilangan Asam")
    show_gravity_specific = fields.Boolean(string="Show Berat Jenis")

class DataHeaderLine(models.Model):
    _name = "data.header.line"
    _description = "Data Header Line"

    name = fields.Char('Name')

class FormDataQc(models.Model):
    _name = "form.data.qc"
    _description = "Form Data QC"

    name = fields.Char('Name')
    type_form = fields.Selection([
        ('raw', 'Bahan Baku'),('half', 'Setengah Jadi'),('finish', 'Bahan Jadi'),('kemas','Bahan Kemas')
        ], string='Tipe Bahan', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    form_lines = fields.One2many('form.data.qc.line', 'form_id', string="Form Lines", copy=True)
    analisa_lines = fields.One2many('form.data.qc.analisa', 'analisa_id', string="Analisa Lines", copy=True)
    revision = fields.Integer('Revisi', default=0)
    state = fields.Selection([
        ('draft', 'Draft'),('active', 'Active')
        ], string='Status', default='draft')
    
    def action_draft(self):
        self.write({'state': 'draft', 'revision': self.revision +1})
    
    def action_active(self):
        self.write({'state': 'active'})

    
class FormDataQcLine(models.Model):
    _name = "form.data.qc.line"
    _description = "Form Data QC Lines"

    form_id = fields.Many2one('form.data.qc', 'Form Data QC', required=True, ondelete='cascade')
    header_id = fields.Many2one('data.header.line', string='Header')
    no_text = fields.Char('No.')
    parameter = fields.Char('Paramater')
    std = fields.Char('Standar')
    result = fields.Char('Hasil Pemeriksaan')
    method = fields.Char(string="Metode")
    decimal_places = fields.Integer("Decimal Places", default="2")

class FormDataQcAlisa(models.Model):
    _name = "form.data.qc.analisa"
    _description = "Form Data QC Analisa"

    analisa_id = fields.Many2one('form.data.qc', 'Form Data QC', required=True, ondelete='cascade')
    no_text = fields.Char('No.')
    rincian_id = fields.Many2one("rincian.analisa", string="Rincian Analisa")
    rincian_code = fields.Char(related="rincian_id.code", string="Code", store=True)
    compute_type = fields.Selection([
        ('berat_jenis', 'Berat Jenis'),('vol_koh', 'Volume KOH'),
        ('sample', 'Sample Massa')
        ], string='Compute type', related="rincian_id.compute_type", store=True)