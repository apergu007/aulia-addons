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


class WizardImportAdjusmentLine(models.TransientModel):
    _name = 'wiz.import.adjusment.line'
    _description = "Import Adjusment Line"

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
        active_id = self.env.context.get('active_id')
        obj_adjustment = self.env["stock.inventory"].browse(active_id)
        obj_import = self.env["stock.inventory.line"]
        pp_obj = self.env['product.product']
        lot_obj = self.env['stock.lot']

        cont = 0
        for row_no in range(sheet.nrows):
            cont += 1
            date_year = False
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

                if not line[0]:
                    raise ValidationError(_(f'Kolom Product harus Di isi'))
                pp_src = pp_obj.search(['|',('name', '=', line[0]),('default_code', '=', line[0])])
                if not pp_src:
                    raise ValidationError(_(f'Product {line[0]} Tidak ditemukan'))
                
                lot_src = False
                if pp_src.is_storable and pp_src.tracking != 'none':
                    if not line[1]:
                        raise ValidationError(_(f'Product {line[0]} Kolom Lot harus Di isi'))
                    
                    lot_src = lot_obj.search([('name', '=', line[1]),('product_id','=',pp_src.id)]).id
                    if not lot_src:
                        lots = {
                            'name': line[1],
                            'product_id': pp_src.id
                        }
                        lot_src = lot_obj.create(lots).id
                lots = lot_src

                data = {
                    'stock_inventory_id': active_id,
                    'product_id'        : pp_src.id,
                    'prod_lot_id'       : lots,
                    'inventory_quantity': line[2],
                }
                obj_import.create(data)