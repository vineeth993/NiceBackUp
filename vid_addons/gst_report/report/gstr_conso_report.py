import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
from openerp import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class gstr_conso_report(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(gstr_conso_report, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'datetime': dt,
			})
		self.context = context

class GstrSummaryReport(report_xls):

	def generate_xls_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		report_name = 'GSTR1 Consolidated Report'
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000

		cr, uid = self.cr, self.uid
		title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')

		invoice_obj = self.pool.get("account.invoice")
		invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0])], order="id asc")
		invoices = invoice_obj.browse(cr, uid, invoice_id)

		b2bTaxable = 0
		b2bIgst = 0
		b2bCgst = 0
		b2bSgst = 0	

		b2cTaxable = 0
		b2cIgst = 0
		b2cCgst = 0
		b2cSgst = 0

		b2tTaxable = 0
		b2tIgst = 0
		b2tCgst = 0
		b2tSgst = 0

		exportTaxableZero = 0
		sezTaxableZero = 0
		deemedTaxableZero = 0
		zeroRated = 0

		exportTaxable = 0
		exportIgst = 0
		exportCgst = 0
		exportSgst = 0

		sezTaxable = 0
		sezIgst = 0
		sezCgst = 0
		sezSgst = 0

		deemedTaxable = 0
		deemedIgst = 0
		deemedCgst = 0
		deemedSgst = 0

		b2bTaxableZero = 0
		b2cTaxableZero = 0
		b2tTaxableZero = 0
		nilRated = 0
		
		if invoice_id:
			for invoice in invoices:
				if 'B2B' in invoice.sale_type_id.name:
					if "SEZ" in invoice.sale_sub_type_id.name:
						for line in invoice.invoice_line:
							if line.invoice_line_tax_id:
								sezTaxable += line.price_subtotal
								for tax in line.invoice_line_tax_id:
									if tax.gst_type == "cgst":
										sezCgst += round((line.price_subtotal * tax.amount), 2)
									elif tax.gst_type == "sgst":
										sezSgst += round((line.price_subtotal * tax.amount), 2)
									elif tax.gst_type == "igst":
										sezIgst += round((line.price_subtotal * tax.amount), 2)

							else:
								sezTaxableZero += line.price_subtotal

					elif 'Deemed' in invoice.sale_sub_type_id.name:
						for line in invoice.invoice_line:
							if line.invoice_line_tax_id:
								deemedTaxable += line.price_subtotal
								for tax in line.invoice_line_tax_id:
									if tax.gst_type == "cgst":
										deemedCgst += round((line.price_subtotal * tax.amount), 2)
									elif tax.gst_type == "sgst":
										deemedSgst += round((line.price_subtotal * tax.amount), 2)
									elif tax.gst_type == "igst":
										deemedIgst += round((line.price_subtotal * tax.amount), 2)

							else:
								deemedTaxableZero += line.price_subtotal

					else:
						for line in invoice.invoice_line:
							if line.invoice_line_tax_id:
								b2bTaxable += line.price_subtotal
								for tax in line.invoice_line_tax_id:
									if tax.gst_type == "cgst":
										b2bCgst += round((line.price_subtotal * tax.amount), 2)
									elif tax.gst_type == "sgst":
										b2bSgst += round((line.price_subtotal * tax.amount), 2)
									elif tax.gst_type == "igst":
										b2bIgst += round((line.price_subtotal * tax.amount), 2)

							else:
								b2bTaxableZero += line.price_subtotal

				elif 'B2C' in invoice.sale_type_id.name:
					for line in invoice.invoice_line:
						if line.invoice_line_tax_id:
							b2cTaxable += line.price_subtotal
							for tax in line.invoice_line_tax_id:
								if tax.gst_type == "cgst":
									b2cCgst += round((line.price_subtotal * tax.amount), 2)
								elif tax.gst_type == "sgst":
									b2cSgst += round((line.price_subtotal * tax.amount), 2)
								elif tax.gst_type == "igst":
									b2cIgst += round((line.price_subtotal * tax.amount), 2)

						else:
							b2cTaxableZero += line.price_subtotal

				elif 'B2T' in invoice.sale_type_id.name:
					for line in invoice.invoice_line:
						if line.invoice_line_tax_id:
							b2tTaxable += line.price_subtotal
							for tax in line.invoice_line_tax_id:
								if tax.gst_type == "cgst":
									b2tCgst += round((line.price_subtotal * tax.amount), 2)
								elif tax.gst_type == "sgst":
									b2tSgst += round((line.price_subtotal * tax.amount), 2)
								elif tax.gst_type == "igst":
									b2tIgst += round((line.price_subtotal * tax.amount), 2)

						else:
							b2tTaxableZero += line.price_subtotal

				elif 'EXP' in invoice.sale_type_id.name:
					for line in invoice.invoice_line:
						if line.invoice_line_tax_id:
							export += line.price_subtotal
							for tax in line.invoice_line_tax_id:
								if tax.gst_type == "cgst":
									exportCgst += round((line.price_subtotal * tax.amount), 2)
								elif tax.gst_type == "sgst":
									exportSgst += round((line.price_subtotal * tax.amount), 2)
								elif tax.gst_type == "igst":
									exportIgst += round((line.price_subtotal * tax.amount), 2)

						else:
							exportTaxableZero += line.price_subtotal				
		name = "GST Sales Summary Report "+str(data['form']["from_date"])+"-"+data['form']["to_date"]
		ws.write(0, 2, name, title2)
		headers = {1:'Taxable Value', 2:'IGST', 3:'CGST', 4:'CGST'}
		for header in headers:
			ws.write(1, header, headers[header], title2)

		ws.write(3, 0, 'With Tax', title2)
		ws.write(5, 0, 'B2B', normal)
		ws.write(5, 1, b2bTaxable, number)
		ws.write(5, 2, b2bIgst, number)
		ws.write(5, 3, b2bCgst, number)
		ws.write(5, 4, b2bSgst, number)

		ws.write(6, 0, 'B2C', normal)
		ws.write(6, 1, b2cTaxable, number)
		ws.write(6, 2, b2cIgst, number)
		ws.write(6, 3, b2cCgst, number)
		ws.write(6, 4, b2cSgst, number)		

		ws.write(7, 0, 'B2T', normal)
		ws.write(7, 1, b2tTaxable, number)
		ws.write(7, 2, b2tIgst, number)
		ws.write(7, 3, b2tCgst, number)
		ws.write(7, 4, b2tSgst, number)	

		ws.write(8, 0, 'Deemed Export With Tax', normal)
		ws.write(8, 1, deemedTaxable, number)
		ws.write(8, 2, deemedIgst, number)
		ws.write(8, 3, deemedCgst, number)
		ws.write(8, 4, deemedSgst, number)

		ws.write(9, 0, 'SEZ With Tax', normal)
		ws.write(9, 1, sezTaxable, number)
		ws.write(9, 2, sezIgst, number)
		ws.write(9, 3, sezCgst, number)
		ws.write(9, 4, sezSgst, number)

		ws.write(10, 0, 'Export With Tax', normal)
		ws.write(10, 1, exportTaxable, number)
		ws.write(10, 2, exportIgst, number)
		ws.write(10, 3, exportCgst, number)
		ws.write(10, 4, exportSgst, number)
		
		ws.write(12, 0, 'Zero rated', title2)
		ws.write(14, 0, 'Deemed Export Without Tax', normal)
		ws.write(14, 1, deemedTaxableZero, number)
		
		ws.write(15, 0, 'SEZ Without Tax', normal)
		ws.write(15, 1, sezTaxableZero, number)
		
		ws.write(16, 0, 'Export Without Tax', normal)
		ws.write(16, 1, exportTaxableZero, number)
		
		zeroRated = deemedTaxableZero + sezTaxableZero + exportTaxableZero
		ws.write(17, 0, 'Zero Rated Total', normal)
		ws.write(17, 1, zeroRated, number)

		ws.write(19, 0, 'Nil Rated', title2)
		ws.write(21, 0, 'B2B Zero Percentage', normal)
		ws.write(21, 1, b2bTaxableZero, number)

		ws.write(22, 0, 'B2C Zero Percentage', normal)
		ws.write(22, 1, b2cTaxableZero, number)

		ws.write(23, 0, 'B2T Zero Percentage', normal)
		ws.write(23, 1, b2tTaxableZero, number)

		nilRated = b2bTaxableZero + b2cTaxableZero + b2tTaxableZero

		ws.write(24, 0, 'Nil Rated Total', normal)
		ws.write(24, 1, nilRated, number)

GstrSummaryReport("report.gstr.consolidated", "gstr.consolidated", parser=gstr_conso_report)