
import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
from openerp import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)

class portal_sale_summary(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(portal_sale_summary, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'datetime': dt,
			})
		self.context = context

class PortalSaleSummary(report_xls):

	def generate_xls_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		normal2          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz centre;')
		number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')
		
		report_name = 'Order Data'
		ws = wb.add_sheet(report_name, cell_overwrite_ok = True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)

		for col in cols:
			ws.col(col).width = 4000

		headers = {0:"Sl No", 1:"Product Code", 2:"Product Name", 3:'Pack', 4:"Quantity (Nos)"}

		for header in headers:
			ws.write(1, header, headers[header], title2)

		if data['form']["order_type"] == "special":
			ws.write(1, 5, 'Special Rate *', title2)

		portal_obj = self.pool.get("portal.sale")
		portal_line_obj = self.pool.get("portal.sale.line")

		portal_sale_id = portal_line_obj.search(cr, uid, [('sale_id', '=', data['form']["id"])], order="id asc")
		portal_line_sale = portal_line_obj.browse(cr, uid, portal_sale_id)

		_logger.info("The portal_sale = "+str(portal_line_sale))
		count = 1
		serial = 0
		for line in portal_line_sale:
			serial += 1
			count += 1
			product = line.product_id.name.rsplit("-", 1)
			ws.write(count, 0, serial, normal)
			ws.write(count, 1, line.product_id.default_code, normal)
			ws.write(count, 2, product[0], normal2)
			ws.write(count, 3, product[1], normal)
			ws.write(count, 4, line.product_qty, normal)
			if data['form']["order_type"] == "special":
				ws.write(count, 5, line.product_price, normal)

PortalSaleSummary('report.portal.excel_report', "portal.sale", parser=portal_sale_summary)
