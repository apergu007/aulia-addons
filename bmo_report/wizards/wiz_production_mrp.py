from dataclasses import Field
import io
import time
import pytz
import base64
import itertools
import xlsxwriter
from io import StringIO

from odoo.tools.misc import xlwt
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from calendar import monthrange
from xlsxwriter.utility import xl_col_to_name

import logging
_logger = logging.getLogger(__name__)

class WizProductionMrp(models.TransientModel):
	_name = "wiz.production.mrp"
	_description = "Report Production MRP"
	
	tipe_produksi = fields.Selection([
		('Mixing', 'Mixing'), ('Filling', 'Filling'), ('Reject', 'Reject')
	], string="Tipe Produksi")
	date_from = fields.Date('Start Date')
	date_to = fields.Date('Start To')

	data_file    = fields.Binary('File')
	name         = fields.Char('File Name')

	def get_data_mixing(self):
		mo_src = self.env['mrp.production']
		start = datetime.combine(self.date_from, datetime.min.time())
		end = datetime.combine(self.date_to, datetime.max.time())
		dom = [('tipe_produksi','=', self.tipe_produksi),('date_finished','>=', start),('date_finished','<=', end),('state','=','done')]

		mo_res = mo_src.search(dom, order='date_finished')
		if not mo_res:
			raise UserError("Tidak ditemukan data produksi pada periode tsb !")

		resul = []
		date_urut = []
		for mo in mo_res:
			date_mo = mo.date_finished.date()
			categ = dict(mo._fields['mrp_type'].selection).get(mo.mrp_type)
			dates_source = ''
			source_mo = mo._get_sources()
			if source_mo:
				dates_source = ', '.join(list(set([x.date_finished.strftime('%d/%m/%y') for x in source_mo])))
			scrap_src = self.env['stock.scrap'].search([('production_id','=', mo.id)])
			scrap_qty = 0 if not scrap_src else round(sum(scrap_src.mapped('scrap_qty')), 2)
			rendemen = 0 if not scrap_src else round((scrap_qty / mo.product_qty) * 100, 2)

			date_urut.append(date_mo.strftime('%d/%m/%y'))
			no_urut = len([x for x in date_urut if x == date_mo.strftime('%d/%m/%y')])
			dat = {
				'Tanggal': date_mo.strftime('%d-%b'), 
				'No Urut': no_urut,
				'Category': categ,
				'Kode Produk': mo.product_id.default_code,
				'No WO': mo.name, 
				'No Batch': '' if not mo.lot_producing_id else mo.lot_producing_id.name, 
				'Quantity (kg)': mo.qty_producing,
				'Target (pcs)': 0 if not source_mo else round(sum(source_mo.mapped('product_qty')), 2),
				'Tgl Mixing': date_mo.strftime('%d/%m/%y'), 
				'Bulk (kg)': scrap_qty, 
				'Rendemen': rendemen, 
				'Tgl OK': dates_source,
			}
			resul.append(dat)
		return resul

	def get_data_filing(self):
		mo_src = self.env['mrp.production']
		start = datetime.combine(self.date_from, datetime.min.time())
		end = datetime.combine(self.date_to, datetime.max.time())
		dom = [('tipe_produksi','=', self.tipe_produksi),('date_finished','>=', start),('date_finished','<=', end),('state','=','done')]

		mo_res = mo_src.search(dom, order='date_finished')
		if not mo_res:
			raise UserError("Tidak ditemukan data produksi pada periode tsb !")

		resul = []
		date_urut = []
		for mo in mo_res:
			date_mo = mo.date_finished.date()
			categ = dict(mo._fields['mrp_type'].selection).get(mo.mrp_type)
			# source_mo = mo._get_sources()
			dates_child = ''
			child_mo = mo._get_children()
			if child_mo:
				dates_child = ', '.join(list(set([x.date_finished.strftime('%d/%m/%y') for x in child_mo])))
			scrap_src = self.env['stock.scrap'].search([('production_id','=', mo.id)])
			scrap_qty = 0 if not scrap_src else round(sum(scrap_src.mapped('scrap_qty')), 2)
			rendemen = 0 if not scrap_src else round((scrap_qty / mo.product_qty) * 100, 2)

			date_urut.append(date_mo.strftime('%d/%m/%y'))
			no_urut = len([x for x in date_urut if x == date_mo.strftime('%d/%m/%y')])
			bln_sebelumnya = bulan_ini = 0
			total = bln_sebelumnya + bulan_ini
			dat = {
				'Tanggal': date_mo.strftime('%d-%b'), 
				'No Urut': no_urut,
				'Category': categ,
				'Kode Produk': mo.product_id.default_code,
				'No WO': mo.name, 
				'No Batch': '' if not mo.lot_producing_id else mo.lot_producing_id.name, 
				'Quantity (kg)': 0 if not child_mo else round(sum(child_mo.mapped('qty_producing')), 2),
				'Target (pcs)': mo.product_qty,
				'Tgl Mixing': dates_child, 
				'Tgl OK': date_mo.strftime('%d/%m/%y'),
				'Tgl Filling': date_mo.strftime('%d/%m/%y'), 
				'Hasil Filling Bulan Sebelumnya': scrap_qty, 
				'Bulan ini': scrap_qty, 
				'Total': total, 
				'Bulk (kg)': scrap_qty, 
				'Bulk terpakai': scrap_qty, 
				'Rendemen filling': rendemen, 
			}
			resul.append(dat)
		return resul
	
	def get_data_reject(self):
		mo_src = self.env['mrp.production']
		start = datetime.combine(self.date_from, datetime.min.time())
		end = datetime.combine(self.date_to, datetime.max.time())
		dom = [('tipe_produksi','=', 'Filling'),('date_finished','>=', start),('date_finished','<=', end),]
		#  ('state','=','done')]

		mo_res = mo_src.search(dom, order='date_finished')
		if not mo_res:
			raise UserError("Tidak ditemukan data produksi pada periode tsb !")
		
		categ_names = []
		scrap_src = self.env['stock.scrap'].search([('production_id','in', mo_res.ids)])
		if scrap_src:
			categ_names = list(set([sc.product_id.categ_id.name for sc in scrap_src]))

		resul = []
		date_urut = []
		for mo in mo_res:
			date_mo = mo.date_finished.date()
			categ = dict(mo._fields['mrp_type'].selection).get(mo.mrp_type)
			# source_mo = mo._get_sources()
			dates_child = ''
			child_mo = mo._get_children()
			if child_mo:
				dates_child = ', '.join(list(set([x.date_finished.strftime('%d/%m/%y') for x in child_mo])))
			scrap_src = self.env['stock.scrap'].search([('production_id','=', mo.id)])
			# scrap_qty = 0 if not scrap_src else round(sum(scrap_src.mapped('scrap_qty')), 2)
			# rendemen = 0 if not scrap_src else round((scrap_qty / mo.product_qty) * 100, 2)

			date_urut.append(date_mo.strftime('%d/%m/%y'))
			no_urut = len([x for x in date_urut if x == date_mo.strftime('%d/%m/%y')])
			bln_sebelumnya = bulan_ini = 0
			total = bln_sebelumnya + bulan_ini
			dat = {
				'Tgl Produksi': date_mo.strftime('%d-%b'), 
				'Category': categ,
				'Kode Produk': mo.product_id.default_code,
				'No WO': mo.name, 
				'No Batch': '' if not mo.lot_producing_id else mo.lot_producing_id.name, 
				'Quantity (kg)': 0 if not child_mo else round(sum(child_mo.mapped('qty_producing')), 2),
				'Target (pcs)': mo.product_qty,
				'Tgl Mixing': dates_child,
				'Tgl OK': date_mo.strftime('%d/%m/%y'),
				'Tgl Filling': date_mo.strftime('%d/%m/%y'), 
				'JUMLAH TURUN BARANG': mo.product_qty, 
				'WO CLOSE': date_mo.strftime('%d/%m/%y'),
			}
			if categ_names:
				for cat in categ_names:
					dat[cat]=0

			if scrap_src:
				for scrap in scrap_src:
					cat_name = scrap.product_id.categ_id.name
					dat[cat_name] += scrap.scrap_qty

			resul.append(dat)
		return resul, categ_names

	def eksport_excel(self):
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory': True})
		# workbook.set_calc_mode('auto')
		# workbook.calc_on_load = True
		sheet = workbook.add_worksheet(f"{self.tipe_produksi}")

		title_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'center'})
		header_left_format = workbook.add_format({
			'bold': True, 'align': 'left', 'valign': 'vcenter',
			# 'bg_color': '#D3D3D3', 'border': 1
		})
		header_table_format = workbook.add_format({
			'bold': True, 'align': 'center', 'valign': 'vcenter',
			'bg_color': '#D3D3D3', 'border': 1
		})
		text_left = workbook.add_format({'align': 'left', 'border': 1})
		text_right = workbook.add_format({'align': 'right', 'border': 1, 'num_format': '#,##0'})
		text_center = workbook.add_format({'align': 'center', 'border': 1})
		text_center_red = workbook.add_format({
			'align': 'center', 'border': 1, 'bg_color': '#FF0000'})
		text_center_num = workbook.add_format({'align': 'center', 'border': 1, 'num_format': '0',})

		# sheet.merge_range("A1:D1", 'Absensi Kehadiran', header_left_format)
		# sheet.merge_range("A2:D2", f"Working Days: {res_data['heads']['wkdy']}", header_left_format)
		# sheet.merge_range("A3:D3", f"Periode: {res_data['heads']['start']} - {res_data['heads']['end']}", header_left_format)

		if self.tipe_produksi == 'Mixing':
			headers_full = [
				'Tanggal', 'No Urut', 'Category', 'Kode Produk',
				'No WO', 'No Batch', 'Quantity (kg)',
				'Target (pcs)', 'Tgl Mixing',  'Bulk (kg)', 'Rendemen', 'Tgl OK',
			]
			headers = [
				'Tanggal', 'No Urut', 'Category', 'Kode Produk', 'No WO', 
				'No Batch', 'Quantity (kg)', 'Target (pcs)', 'Tgl Mixing',
			]
			no = 0
			co = 0
			for h in headers:
				sheet.merge_range(no, co, no+1, co, h, text_center)
				# sheet.merge_range(f"A{no}:A{no+1}", h, text_center)
				# sheet.write(no, co, h, text_center)
				co+=1
			sheet.merge_range(no, co, no, co+1, 'Hasil', text_center)
			sheet.write(no+1, co, 'Bulk (kg)', text_center)
			sheet.write(no+1, co+1, 'Rendemen', text_center)
			sheet.merge_range(no, co+2, no+1, co+2, 'Tgl OK', text_center)
		
			no = 2
			list_sum = {}
			res_data = self.get_data_mixing()
			# print(res_data,'ssssssssssssss')
			for res in res_data:
				co = 0
				for k,y in res.items():
					sheet.write(no, co, f'{y} %' if k == 'Rendemen' else y, text_center)
					if k in ['Quantity (kg)','Target (pcs)','Rendemen']:
						if not k in list_sum:
							list_sum[k] = [y]
						else:
							list_sum[k].append(y)
					co+=1
				no+=1

			no_sum = no+1
			no_sum_line = no_sum-1
			avg_rendemen = 0 if not 'Rendemen' in list_sum else round(sum(list_sum['Rendemen']) / len(list_sum['Rendemen']), 2)
			sheet.merge_range(f"A{no_sum}:F{no_sum}", 'TOTAL', text_center)
			# sheet.write(no_sum, co, 'Bulk (kg)', text_center)
			sheet.write(f"G{no_sum}", sum(list_sum['Quantity (kg)']), text_center)
			sheet.write(f"H{no_sum}", sum(list_sum['Target (pcs)']), text_center)
			sheet.write(f"K{no_sum}", f'{avg_rendemen} %', text_center)

		elif self.tipe_produksi == 'Filling':
			headers = [
				'Tgl Wo', 'No Urut', 'Category', 'Kode Produk',
				'No WO', 'No Batch', 'Quantity (kg)',
				'Target (pcs)', 'Tgl Mixing', 'Tgl OK', 'Tgl Filling', 'Hasil Filling Bulan Sebelumnya'
			]
			mini_head = [
				'Bulan ini', 'Total', 'Bulk (kg)', 'Bulk terpakai', 'Rendemen Filling'
			]
			ls = ['Quantity (kg)','Target (pcs)','Bulan ini','Total','Bulk (kg)','Hasil Filling Bulan Sebelumnya']
			no = 0
			co = 0
			for h in headers:
				sheet.merge_range(no, co, no+1, co, h, text_center)
				co+=1

			sheet.merge_range(no, co, no, co+len(mini_head)-1, 'Hasil Filling Bulan Ini', text_center)
			co_h = co
			for h in mini_head:
				sheet.write(no+1, co_h, h, text_center)
				co_h+=1

			no = 2
			list_sum = {}
			res_data = self.get_data_filing()
			for res in res_data:
				co = 0
				for k,y in res.items():
					sheet.write(no, co, f'{y} %' if k == 'Yield (%)' else y, text_center)
					if k in ls:
						if not k in list_sum:
							list_sum[k] = [y]
						else:
							list_sum[k].append(y)
					co+=1
				no+=1

			no_sum = no+1
			total = round(sum(list_sum['Bulan ini']) + sum(list_sum['Hasil Filling Bulan Sebelumnya']), 2)
			sheet.merge_range(f"A{no_sum}:F{no_sum}", 'TOTAL', text_center)
			# sheet.write(no_sum, co, 'Bulk (kg)', text_center)
			sheet.write(f"G{no_sum}", sum(list_sum['Quantity (kg)']), text_center)
			sheet.write(f"H{no_sum}", sum(list_sum['Target (pcs)']), text_center)
			sheet.write(f"L{no_sum}", sum(list_sum['Bulan ini']), text_center)
			sheet.write(f"M{no_sum}", sum(list_sum['Bulan ini']), text_center)
			sheet.write(f"N{no_sum}", f'{total}', text_center)
		
		elif self.tipe_produksi == 'Reject':
			headers = [
				'Tgl Produksi',	'Category',	'Kode Produk', 'NO WO',	'NO BATCH',	'Quantity (KG)', 'Target (pcs)',
				'Tgl Mixing', 'Tgl OK',	'Tgl Filling', 'JUMLAH TURUN BARANG', 'WO CLOSE'
			]
			no = 0
			co = 0
			for h in headers:
				sheet.merge_range(no, co, no+1, co, h, text_center)
				co+=1

			res_data = self.get_data_reject()
			for cat in res_data[1]:
				sheet.merge_range(no, co, no+1, co, cat, text_center)
				co+=1

			no = 2
			list_sum = {}
			ls = ['Quantity (kg)','Target (pcs)','JUMLAH TURUN BARANG']
			for res in res_data[0]:
				co = 0
				for k,y in res.items():
					sheet.write(no, co, y, text_center)
					if k in ls or res_data[1]:
						if not k in list_sum:
							list_sum[k] = [y]
						else:
							list_sum[k].append(y)
					co+=1
				no+=1

			no_sum = no+1
			sheet.merge_range(f"A{no_sum}:E{no_sum}", 'TOTAL', text_center)
			sheet.write(f"F{no_sum}", sum(list_sum[f'{ls[0]}']), text_center)
			sheet.write(f"G{no_sum}", sum(list_sum[f'{ls[1]}']), text_center)
			sheet.write(f"K{no_sum}", sum(list_sum[f'{ls[2]}']), text_center)
			if res_data[1]:
				start_col = 12  # M
				for i in range(len(res_data[1])):
					col_letter = xl_col_to_name(start_col + i)
					sheet.write(f"{col_letter}{no_sum}", sum(list_sum[f'{res_data[1][i]}']), text_center)
					# sheet.write_formula(f"{col_letter}{no_sum}", f"=SUM({col_letter}3:{col_letter}{no})", text_center_num)

		sheet.set_column(0, 0, 5)
		for i in range(19):
			sheet.set_column(i, i, 20)

		workbook.close()
		output.seek(0)
		out = base64.encodebytes(output.read())

		filename = f'Report {self.tipe_produksi} Periode {self.date_from} - {self.date_to}.xlsx'
		self.write({'data_file': out, 'name': filename})

		view = self.env.ref('bmo_report.view_wiz_production_mrp')
		return {
			'view_type': 'form',
			'views': [(view.id, 'form')],
			'view_mode': 'form',
			'res_id': self.id,
			'res_model': 'wiz.production.mrp',
			'type': 'ir.actions.act_window',
			'target': 'new',
		}