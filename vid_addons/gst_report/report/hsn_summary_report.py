import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
import datetime
from openerp import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class sale_hsn_summary(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(sale_hsn_summary, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'datetime': dt,
			})
		self.context = context
	

class HsnReport(report_xls):

	def annual_hsn_summary(self, invoice_obj, cr, uid, wb, data):

		report_name = 'HSN Sale Summary Report '
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000

		headers = {0:"HSN", 1:"Description", 2:'UQC', 3:"Total Quantity", 4:'Total Value', 5:'Taxable Value', 6:'Tax(%)', 7:'Integrated Tax Amount', 8:'Central Tax Amount', 9:'State/UT Tax Amount', 10:'Cess Amount'}

		for header in headers:
			ws.write(3, header, headers[header], self.title2)

		hsn_line = data['form']['hsn_line']
		invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0])])
		invoices = invoice_obj.browse(cr, uid, invoice_id)
		hsn_obj = self.pool.get("hs.code")
		hsn_search = hsn_obj.search(cr, uid, [])
		hsn_code_id = hsn_obj.browse(cr, uid, hsn_search)
		hsn_temp = []
		
		hsn_total_taxable = 0
		hsn_total_amount = 0
		hsn_total_igst = 0
		hsn_total_cgst = 0
		hsn_total_sgst = 0
		hsn_total_cess = 0
		hsn_count = 0
		hsn_dict = {}

		count = 4

		tax_perc = 0

		if invoice_id:
			for invoice in invoices:
				for line in invoice.invoice_line:

					hsn_cgst_total = 0
					hsn_sgst_total = 0
					hsn_igst_total = 0
					hsn_cess_total = 0
					hsn_taxed = 0

					if line.invoice_line_tax_id:
						for tax in line.invoice_line_tax_id:
							if tax.gst_type == "cgst":
								hsn_cgst_total = round((line.price_subtotal * tax.amount), 2)
								tax_perc = tax.amount * 2 * 100
							elif tax.gst_type == "sgst":
								hsn_sgst_total = round((line.price_subtotal * tax.amount), 2)
								tax_perc = tax.amount * 2 * 100
							elif tax.gst_type == "igst":
								hsn_igst_total = round((line.price_subtotal * tax.amount), 2)
								tax_perc = tax.amount * 100
							# elif tax.gst_type == "cess":
							# 	hsn_cess_total = round((line.price_subtotal * tax.amount), 2)
							else:
								tax_perc = 0
					else:
						tax_perc = 0		

					hsn_taxed = line.price_subtotal + hsn_cgst_total + hsn_sgst_total + hsn_igst_total + hsn_cess_total
					hsn_parsed = line.product_id.hs_code_id.code[0:hsn_line]
					if hsn_dict.get(hsn_parsed):
						if hsn_dict[hsn_parsed].get(tax_perc):
							hsn_dict[hsn_parsed][tax_perc][0] += line.quantity
							hsn_dict[hsn_parsed][tax_perc][1] += line.price_subtotal
							hsn_dict[hsn_parsed][tax_perc][2] += hsn_cgst_total
							hsn_dict[hsn_parsed][tax_perc][3] += hsn_sgst_total
							hsn_dict[hsn_parsed][tax_perc][4] += hsn_igst_total
							hsn_dict[hsn_parsed][tax_perc][5] += hsn_cess_total
							hsn_dict[hsn_parsed][tax_perc][6] += hsn_taxed
						else:
							hsn_dict[hsn_parsed].update({tax_perc:[line.quantity, line.price_subtotal, hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total, hsn_taxed, line.product_id.hs_code_id.description]})
					else:
						hsn_count += 1
						hsn_dict[hsn_parsed] = {tax_perc:[line.quantity, line.price_subtotal, hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total, hsn_taxed, line.product_id.hs_code_id.description]}
					
					hsn_total_taxable += line.price_subtotal
					hsn_total_amount += hsn_taxed
					hsn_total_igst += hsn_igst_total
					hsn_total_cgst += hsn_cgst_total
					hsn_total_sgst += hsn_sgst_total
					hsn_total_cess += hsn_cess_total

		for hsn in hsn_dict:
			for tax in hsn_dict[hsn]:
				ws.write(count, 0, hsn, self.number2d)
				ws.write(count, 1, hsn_dict[hsn][tax][7], self.normal)
				ws.write(count, 2, 'NOS-NUMBERS', self.normal)
				ws.write(count, 3, hsn_dict[hsn][tax][0], self.number2d)
				ws.write(count, 4, hsn_dict[hsn][tax][6], self.number2d)
				ws.write(count, 5, hsn_dict[hsn][tax][1], self.number2d)
				ws.write(count, 6, tax, self.number2d)
				ws.write(count, 7, hsn_dict[hsn][tax][4], self.number2d)
				ws.write(count, 8, hsn_dict[hsn][tax][2], self.number2d)
				ws.write(count, 9, hsn_dict[hsn][tax][3], self.number2d)
				ws.write(count, 10, hsn_dict[hsn][tax][5], self.number2d)
				count += 1

		ws.write(0, 0, 'Summary For HSN(12)', self.title2)
		headers = {0:"No.of HSN", 4:'Total Value', 5:'Taxable Value', 7:'Total Integrated Tax', 8:'Total Central Tax', 9:'Total State/UT Tax', 10:'Total Cess'}
		for header in headers:
			ws.write(1, header, headers[header], self.title2)
		ws.write(2, 0, hsn_count, self.number2d)
		ws.write(2, 4, round(hsn_total_amount, 2), self.number2d)
		ws.write(2, 5, round(hsn_total_taxable, 2), self.number2d)
		ws.write(2, 7, round(hsn_total_igst, 2), self.number2d)
		ws.write(2, 8, round(hsn_total_cgst, 2), self.number2d)
		ws.write(2, 9, round(hsn_total_sgst, 2), self.number2d)
		ws.write(2, 10, round(hsn_total_cess, 2), self.number2d)

	def monthly_hsn_summary(self, invoice_obj, cr, uid, wb, data):

		report_name = 'HSN Sale Summary Report '
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000

		headers = {0:"HSN", 1:"Description", 2:'UQC', 3:"Total Quantity", 4:'Total Value', 5:'Taxable Value', 6: 'Tax %', 7:'Integrated Tax Amount', 8:'Central Tax Amount', 9:'State/UT Tax Amount', 10:'Cess Amount'}

		for header in headers:
			ws.write(3, header, headers[header], self.title2)

		hsn_line = data['form']['hsn_line']
		invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0])])
		invoices = invoice_obj.browse(cr, uid, invoice_id)
		hsn_obj = self.pool.get("hs.code")
		hsn_search = hsn_obj.search(cr, uid, [])
		hsn_code_id = hsn_obj.browse(cr, uid, hsn_search)
		hsn_temp = []
		
		hsn_total_taxable = 0
		hsn_total_amount = 0
		hsn_total_igst = 0
		hsn_total_cgst = 0
		hsn_total_sgst = 0
		hsn_total_cess = 0
		hsn_count = 0
		hsn_dict = {}

		count = 4

		tax_perc = 0

		if invoice_id:
			for invoice in invoices:
				for line in invoice.invoice_line:

					hsn_cgst_total = 0
					hsn_sgst_total = 0
					hsn_igst_total = 0
					hsn_cess_total = 0
					hsn_taxed = 0

					if line.invoice_line_tax_id:
						for tax in line.invoice_line_tax_id:
							if tax.gst_type == "cgst":
								hsn_cgst_total = round((line.price_subtotal * tax.amount), 2)
								tax_perc = tax.amount * 2 * 100
							elif tax.gst_type == "sgst":
								hsn_sgst_total = round((line.price_subtotal * tax.amount), 2)
								tax_perc = tax.amount * 2 * 100
							elif tax.gst_type == "igst":
								hsn_igst_total = round((line.price_subtotal * tax.amount), 2)
								tax_perc = tax.amount * 100
							# elif tax.gst_type == "cess":
							# 	hsn_cess_total = round((line.price_subtotal * tax.amount), 2)
							else:
								tax_perc = 0
					else:
						tax_perc = 0		

					hsn_parsed = line.product_id.hs_code_id.code[0:hsn_line]
					hsn_taxed = line.price_subtotal + hsn_cgst_total + hsn_sgst_total + hsn_igst_total + hsn_cess_total
					if hsn_dict.get(hsn_parsed):
						if hsn_dict[hsn_parsed].get(tax_perc):
							hsn_dict[hsn_parsed][tax_perc][0] += line.quantity
							hsn_dict[hsn_parsed][tax_perc][1] += line.price_subtotal
							hsn_dict[hsn_parsed][tax_perc][2] += hsn_cgst_total
							hsn_dict[hsn_parsed][tax_perc][3] += hsn_sgst_total
							hsn_dict[hsn_parsed][tax_perc][4] += hsn_igst_total
							hsn_dict[hsn_parsed][tax_perc][5] += hsn_cess_total
							hsn_dict[hsn_parsed][tax_perc][6] += hsn_taxed
						else:
							hsn_dict[hsn_parsed].update({tax_perc:[line.quantity, line.price_subtotal, hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total, hsn_taxed, line.product_id.hs_code_id.description]})
					else:
						hsn_count += 1
						hsn_dict[hsn_parsed] = {tax_perc:[line.quantity, line.price_subtotal, hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total, hsn_taxed, line.product_id.hs_code_id.description]}
					
					hsn_total_taxable += line.price_subtotal
					hsn_total_amount += hsn_taxed
					hsn_total_igst += hsn_igst_total
					hsn_total_cgst += hsn_cgst_total
					hsn_total_sgst += hsn_sgst_total
					hsn_total_cess += hsn_cess_total

		for hsn in hsn_dict:
			for tax in hsn_dict[hsn]:
				ws.write(count, 0, hsn, self.number2d)
				ws.write(count, 1, hsn_dict[hsn][tax][7], self.normal)
				ws.write(count, 2, 'NOS-NUMBERS', self.normal)
				ws.write(count, 3, hsn_dict[hsn][tax][0], self.number2d)
				ws.write(count, 4, hsn_dict[hsn][tax][6], self.number2d)
				ws.write(count, 5, hsn_dict[hsn][tax][1], self.number2d)
				ws.write(count, 6, tax, self.number2d)
				ws.write(count, 7, hsn_dict[hsn][tax][4], self.number2d)
				ws.write(count, 8, hsn_dict[hsn][tax][2], self.number2d)
				ws.write(count, 9, hsn_dict[hsn][tax][3], self.number2d)
				ws.write(count, 10, hsn_dict[hsn][tax][5], self.number2d)
				count += 1

		ws.write(0, 0, 'Summary For HSN(12)', self.title2)
		headers = {0:"No.of HSN", 4:'Total Value', 5:'Taxable Value', 7:'Total Integrated Tax', 8:'Total Central Tax', 9:'Total State/UT Tax', 10:'Total Cess'}
		for header in headers:
			ws.write(1, header, headers[header], self.title2)
		ws.write(2, 0, hsn_count, self.number2d)
		ws.write(2, 4, round(hsn_total_amount, 2), self.number2d)
		ws.write(2, 5, round(hsn_total_taxable, 2), self.number2d)
		ws.write(2, 7, round(hsn_total_igst, 2), self.number2d)
		ws.write(2, 8, round(hsn_total_cgst, 2), self.number2d)
		ws.write(2, 9, round(hsn_total_sgst, 2), self.number2d)
		ws.write(2, 10, round(hsn_total_cess, 2), self.number2d)

	def generate_xls_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		self.title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		self.normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		self.number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		self.number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		self.number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')
		
		invoice_obj = self.pool.get("account.invoice")
		if  data['form']["report_type"] == "annually":
			self.annual_hsn_summary(invoice_obj, cr, uid, wb, data)
		elif data['form']["report_type"] == "monthly":
			self.monthly_hsn_summary(invoice_obj, cr, uid, wb, data)

HsnReport('report.gstr.hsn_report', "gstr.hsn_report", parser=sale_hsn_summary)
