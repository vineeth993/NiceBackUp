import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
from openerp import api, models, fields, _
import logging


_logger = logging.getLogger(__name__)

class cess_summary_report(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(cess_summary_report, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'datetime': dt,
			})
		self.context = context

class CessSummary(report_xls):

	def generate_xls_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		self.title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		self.normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		self.number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		self.number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		self.number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')

		heading = "Cess from "+ str(data['form']["from_date"]) + " to " + data['form']["to_date"]

		report_name = 'CESS Sale Summary Report '
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000

		ws.write(1, 1, heading, self.title2)
		
		invoice_obj = self.pool.get('account.invoice')
		invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company_id'][0]), ("sale_type_id", "=" , data['form']["sale_order_type"][0]), ("sale_sub_type_id", "=", data['form']["sale_sub_type"][0])], order="id asc")
		invoices = invoice_obj.browse(cr, uid, invoice_id)

		headers = {0:"TAX(%)", 1:"Taxable Value", 2:"CESS Value"}
		tax_dict = {}

		count = 4

		for header in headers:
			ws.write(3, header, headers[header], self.title2)

		for invoice in invoices:

			for line in invoice.invoice_line:
				tax_perc = 0
				cess_state = 0
				if line.invoice_line_tax_id:
					for tax in line.invoice_line_tax_id:
						if tax.gst_type in ["sgst", "cgst"]:
							tax_perc = tax.amount * 100
						if tax.gst_type == "cess":
							cess_state = 1
				_logger.info("The tax_perc = "+str(tax_perc))
				_logger.info("The taxable amount = "+str(line.price_subtotal))
				if cess_state:
					if tax_dict.get(tax_perc):
						tax_dict[tax_perc] += line.price_subtotal
					else:
						tax_dict.update({tax_perc:line.price_subtotal})

		for tax in tax_dict:
			cess = tax_dict[tax] / 100
			ws.write(count, 0, tax, self.number2d)
			ws.write(count, 1, tax_dict[tax], self.number2d)
			ws.write(count, 2, cess, self.number2d)

			count += 1

CessSummary('report.cess_sale.report', "cess_sale.report", parser=cess_summary_report)

