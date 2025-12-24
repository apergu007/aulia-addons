import time
import tempfile
import binascii
import itertools
import xlrd
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, exceptions, api,_
from dateutil.relativedelta import *
import io
import logging
_logger = logging.getLogger(__name__)
import string

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class WizardImportAttendances(models.TransientModel):
    _name = 'wiz.import.master.qc'
    _description = "Import Absen"

    file_data = fields.Binary('File')
    file_name = fields.Char('File Name')
    
    def import_data(self):
        if not self.file_name:
            raise ValidationError(_('Unselected file'))
        
        fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file_data))
        fp.seek(0)

        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        obj_import = self.env["form.data.qc"]
        obj_line_import = self.env["form.data.qc.line"]
        active_id = self.env.context.get('active_id')
        analisa_line = self.env["form.data.qc.analisa"]
        header_line_src = self.env['data.header.line']
        rincian_src = self.env['rincian.analisa']
        qc_data = self.env[obj_import].browse(active_id)

        cont = 0
        for row_no in range(sheet.nrows):
            cont += 1
            date_year = False
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

                header_src = header_line_src.search([('name', '=', line[1])], limit=1)
                if not header_src:
                    raise ValidationError(_(f'Data {line[1]} Tidak ditemukan'))

                data = {
                    'form_id'   : active_id,
                    'no_text'   : line[0],
                    'header_id' : header_src.id,
                    'parameter' : line[2],
                    'std'       : line[3],
                }
                obj_line_import.create(data)
        
        sheet_analisa = workbook.sheet_by_index(1)
        if qc_data.type_form == 'raw':
            cont = 0
            for row_no in range(sheet_analisa.nrows):
                cont += 1
                date_year = False
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet_analisa.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet_analisa.row(row_no)))

                    rincian_id = rincian_src.search([('name', '=', line[1])], limit=1)
                    if not rincian_id:
                        raise ValidationError(_(f'Data {line[1]} Tidak ditemukan'))

                    data = {
                        'analisa_id'   : active_id,
                        'no_text'   : line[0],
                        'rincian_id' : rincian_id.id,
                    }
                    analisa_line.create(data)