# -*- encoding: utf-8 -*-

import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
import datetime

import logging

_logger = logging.getLogger(__name__)

def get_ratio(no1, no2):
	if no2 != 0:
		return no1 / no2
	return 0

class sale_status_report_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(sale_status_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'datetime': dt,
			})
		self.context = context
	
class sale_status_report(report_xls):
	
	def generate_xls_report(self, parser, xls_styles, data, objects, wb):

		if data['form']['prod_or_cust'] == 'cust':
			self.customer_pending_report(parser, xls_styles, data, objects, wb)
		elif data['form']['prod_or_cust'] == 'prod':
			self.product_pending_report(parser, xls_styles, data, objects, wb)
		elif  data['form']['prod_or_cust'] == 'all':
			self.all_product_pending_report(parser, xls_styles, data, objects, wb)
		elif data['form']['prod_or_cust'] == 'all_order':
			self.all_order_pending_report(parser, xls_styles, data, objects, wb)

	def customer_pending_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		report_name = 'Sale Summary Report ' + '-' + time.strftime('%d-%m-%Y')
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000
		ws.col(1).width = 5000
		ws.col(2).width = 5000
		ws.col(4).width = 10000
		
		title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		normal_order    = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		normal_name     = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		normal_center   = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz center;')
		number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')

		sale_obj = self.pool.get('sale.order')
		picking_obj = self.pool.get('stock.picking')
		if 'object' in data:
			sale_ids = data['object']
		else:
			sale_ids = sale_obj.search(cr, uid, [('state', 'not in', ('draft', 'cancel', 'done', 'shipping_except')),
				('date_order', '>=', data['form']['date_from']), ('date_order', '<=', data['form']['date_to']),("partner_id", "=", int(data['form']['customer'][0]))
				])
		count = 2

		sales = sale_obj.browse(cr, uid, sale_ids)

		from_date = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d').date().strftime('%d-%m-%Y')
		to_date = datetime.datetime.strptime(data['form']['date_to'], '%Y-%m-%d').date().strftime('%d-%m-%Y')

		name = "Pending Sale Order status for "+str(data['form']['customer'][1]) + " from " +from_date+" to "+to_date

		ws.write(0, 0, name, title2)

		headers = {
			0: 'Sale Order Date', 1: 'Sale Order No', 2:'Order Ref', 3:'PCode', 4: 'Product', 5:'Pack', 6: 'Order Qty', 7: 'Issued Qty.', 8: 'Pending Qty.',
			}
  
		for header in headers:
			ws.write(count , header, headers[header], title2)

		count = count + 1
		invoiceQty = {}
		orderLineQty = {}
		stockQty = {}
		for sale in sales:
			stock_ids = picking_obj.search(cr, uid, [('state', 'not in', ('cancel', 'done')), ('origin', '=', sale.name)])
			stocks = picking_obj.browse(cr, uid, stock_ids)
			# stockQty = {line.product_id.name:line.product_uom_qty for line in stocks.move_lines}
			date = datetime.datetime.strptime(sale.date_order, '%Y-%m-%d %H:%M:%S').date().strftime('%d-%m-%Y')
			for invoice in sale.invoice_ids:
				for line in invoice.invoice_line:
					if invoiceQty.has_key(str(line.product_id.name)):
						invoiceQty[str(line.product_id.name)] += line.quantity
					else:
						invoiceQty.update({str(line.product_id.name):line.quantity})
			for line in sale.order_line:
				if orderLineQty.has_key(str(line.product_id.name)):
					orderLineQty[str(line.product_id.name)][0] += line.product_uom_qty
				else:
					orderLineQty.update({str(line.product_id.name):[line.product_uom_qty, line.discount, line.extra_discount, line.additional_discount, line.product_id.default_code]})

			for stock in stocks:
				for line in stock.move_lines:
					if stockQty.has_key(str(line.product_id.name)):
						stockQty[str(line.product_id.name)] += line.product_uom_qty
					else:
						stockQty.update({str(line.product_id.name):line.product_uom_qty})

			for orderLine in orderLineQty:
				if stockQty.has_key(orderLine):
					quantityPending = stockQty[orderLine]
					if invoiceQty.has_key(orderLine):
						issuedQuan = invoiceQty[orderLine]
					else:
						issuedQuan = 0

					if quantityPending > 0:
						ws.write(count, 0, date, normal_center)
						ws.write(count, 1, sale.name, normal_order)
						ws.write(count, 2, sale.client_order_ref, normal_order)
						ws.write(count, 3, orderLineQty[orderLine][4], normal_center)
						ws.write(count, 4, orderLine.rsplit('-', 1)[0], normal_name)
						ws.write(count, 5, orderLine.rsplit('-', 1)[1], normal_center)
						ws.write(count, 6, orderLineQty[orderLine][0], normal_center)
						ws.write(count, 7, issuedQuan, normal_center)
						ws.write(count, 8, quantityPending, normal_center)
						count += 1
			invoiceQty = {}
			orderLineQty = {}
			stockQty = {}

	def product_pending_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		report_name = 'Sale Summary Report' + '-' + time.strftime('%d-%m-%Y')
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000
		title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')

		sale_obj = self.pool.get('sale.order')
		picking_obj = self.pool.get('stock.picking')
		if 'object' in data:
			sale_ids = data['object']
		else:
			sale_ids = sale_obj.search(cr, uid, [('state', 'not in', ('draft', 'cancel', 'done', 'shipping_except')),
				('date_order', '>=', data['form']['date_from']), ('date_order', '<=', data['form']['date_to']), ("order_line", "=", data['form']['product'][1]),
				('company_id', '=', data['form']['company_id'][0])])
		count = 3


		sales = sale_obj.browse(cr, uid, sale_ids)

		from_date = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d').date().strftime('%d-%m-%Y')
		to_date = datetime.datetime.strptime(data['form']['date_to'], '%Y-%m-%d').date().strftime('%d-%m-%Y')

		name = "Pending Sale Order status for "+str(data['form']['product'][1]) + "from " +from_date+" to "+to_date
		ws.write(0, 0, name, title2)

		headers = {
			0: 'Customer', 1: 'Sale Order No', 2: 'Order Date', 3: 'Order Qty.', 4: 'Issued Qty.', 5: 'Pending Qty.',
			}
		orderLineQty = {}
		invoiceQty = {}
		issuedQuan = 0
		for header in headers:
			ws.write(count , header, headers[header], title2)
		count += 1
		for sale in sales:
			date = datetime.datetime.strptime(sale.date_order, '%Y-%m-%d %H:%M:%S').date().strftime('%d-%m-%Y')
			for line in sale.order_line:
				if line.product_id.id != data['form']['product'][0]:
					continue
				if orderLineQty.has_key(str(sale.partner_id.name)):
					orderLineQty[sale.partner_id.name] += line.product_uom_qty
				else:
					orderLineQty.update({str(sale.partner_id.name):line.product_uom_qty})
			for invoice in sale.invoice_ids:
				for line in invoice.invoice_line:
					if line.product_id.id != data['form']['product'][0]:
						continue                    
					if invoiceQty.has_key(str(line.product_id.name)):
						invoiceQty[str(line.product_id.name)] += line.quantity
					else:
						invoiceQty.update({str(invoice.partner_id.name):line.quantity})
			for order in orderLineQty:
				if invoiceQty.has_key(str(order)):
					pendingQuant = orderLineQty[order] - invoiceQty[order]
				else:
					pendingQuant = 0
				if pendingQuant > 0:
					ws.write(count, 0, order, normal)
					ws.write(count, 1, sale.name, normal)
					ws.write(count, 2, date, normal)
					ws.write(count, 3, orderLineQty[order], normal)
					ws.write(count, 4, invoiceQty[order], normal)
					ws.write(count, 5, pendingQuant, normal)
					count += 1
			
			orderLineQty = {}
			invoiceQty = {}        

	def all_product_pending_report(self, parser, xls_styles, data, objects, wb):
		
		cr, uid = self.cr, self.uid
		report_name = 'Sale Summary Report' + '-' + time.strftime('%d-%m-%Y')
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000
		title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		title1 			= xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz left;')
		normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')

		sale_obj = self.pool.get('sale.order')
		picking_obj = self.pool.get('stock.picking')
		
		product_obj = self.pool.get("product.product")
		product_search = product_obj.search(cr, uid, [])
		product_id = product_obj.browse(cr, uid, product_search)
		
		count = 1
		sheet = 1

		orderLineQty = {}
		invoiceQty = {}
		issuedQuan = 0
		
		from_date = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d').date().strftime('%d-%m-%Y')
		to_date = datetime.datetime.strptime(data['form']['date_to'], '%Y-%m-%d').date().strftime('%d-%m-%Y')

		heading = "Pending Sales Order Status from "+str(from_date)+" to "+str(to_date)

		ws.write(count , 0, heading, title1)

		headers = {
				0: 'Product.', 1: 'Sale Order no.', 2: 'Order Date', 3: 'Order Qty.', 4: 'Issued QTY.', 5: 'Pending Qty',
				}
		count += 2
		for header in headers:
			ws.write(count , header, headers[header], title2)
		count += 1

		for product in product_id:

			name = "["+str(product.default_code)+"] "+product.name
			sale_ids = sale_obj.search(cr, uid, [('state', 'not in', ('draft', 'cancel', 'done', 'shipping_except')),
					('date_order', '>=', data['form']['date_from']), ('date_order', '<=', data['form']['date_to']), ("order_line", "=", name),
					('company_id', '=', data['form']['company_id'][0])])

			sales = sale_obj.browse(cr, uid, sale_ids)

			if not sales:
				continue
			count += 1
			ws.write(count , 0, str(product.name), title1)
			count += 2
			# count += 2

			for sale in sales:
				date = datetime.datetime.strptime(sale.date_order, '%Y-%m-%d %H:%M:%S').date().strftime('%d-%m-%Y')
				for line in sale.order_line:
					if line.product_id.id != product.id:
						continue
					if orderLineQty.has_key(str(sale.partner_id.name)):
						orderLineQty[sale.partner_id.name] += line.product_uom_qty
					else:
						orderLineQty.update({str(sale.partner_id.name):line.product_uom_qty})
				for invoice in sale.invoice_ids:
					for line in invoice.invoice_line:
						if line.product_id.id != product.id:
							continue                    
						if invoiceQty.has_key(str(line.product_id.name)):
							invoiceQty[str(line.product_id.name)] += line.quantity
						else:
							invoiceQty.update({str(invoice.partner_id.name):line.quantity})
				for order in orderLineQty:
					if invoiceQty.has_key(str(order)):
						pendingQuant = orderLineQty[order] - invoiceQty[order]
					else:
						issuedQuan = 0

					if pendingQuant >= 0:
						name = order + " , " +str(sale.partner_id.city_id.name)
						ws.write(count, 0, name, normal)
						ws.write(count, 1, sale.name, normal)
						ws.write(count, 2, date, normal)
						ws.write(count, 3, orderLineQty[order], normal)
						ws.write(count, 4, (invoiceQty[order]), normal)
						ws.write(count, 5, pendingQuant, normal)
						count += 1
				orderLineQty = {}
				invoiceQty = {}

	def all_order_pending_report(self, parser, xls_styles, data, objects, wb):

		cr, uid = self.cr, self.uid
		report_name = 'Sale Summary Report' + '-' + time.strftime('%d-%m-%Y')
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)
		for col in cols:
			ws.col(col).width = 4000
		title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
		title1 			= xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz left;')		
		normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
		number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')		
		
		count = 1
		sheet = 1

		orderLineQty = {}
		invoiceQty = {}
		issuedQuan = 0
		
		from_date = datetime.datetime.strptime(data['form']['date_from'], '%Y-%m-%d').date().strftime('%d-%m-%Y')
		to_date = datetime.datetime.strptime(data['form']['date_to'], '%Y-%m-%d').date().strftime('%d-%m-%Y')

		heading = "Pending Sales Order Status from "+str(from_date)+" to "+str(to_date)

		ws.write(count , 0, heading, title1)

		headers = {
				0: 'Customer.', 1: 'Sale Order no.', 2: 'Order Date.', 3:'Product.',4: 'Order Qty.', 5: 'Issued QTY.', 6: 'Pending Qty.',
				}
		count += 2

		for header in headers:
			ws.write(count , header, headers[header], title2)		

		sale_obj = self.pool.get('sale.order')
		picking_obj = self.pool.get('stock.picking')
		if 'object' in data:
			sale_ids = data['object']
		else:
			sale_ids = sale_obj.search(cr, uid, [('state', 'not in', ('draft', 'cancel', 'done', 'shipping_except')),
				('date_order', '>=', data['form']['date_from']), ('date_order', '<=', data['form']['date_to']), ('company_id', '=', data['form']['company_id'][0])])
		count = 3
		
		sales = sale_obj.browse(cr, uid, sale_ids)
		count = count + 1
		invoiceQty = {}
		orderLineQty = {}
		stockQty = {}
		for sale in sales:
			stock_ids = picking_obj.search(cr, uid, [('state', 'not in', ('cancel', 'done')), ('origin', '=', sale.name)])
			stocks = picking_obj.browse(cr, uid, stock_ids)
			# stockQty = {line.product_id.name:line.product_uom_qty for line in stocks.move_lines}
			date = datetime.datetime.strptime(sale.date_order, '%Y-%m-%d %H:%M:%S').date().strftime('%d-%m-%Y')
			for invoice in sale.invoice_ids:
				for line in invoice.invoice_line:
					if invoiceQty.has_key(str(line.product_id.name)):
						invoiceQty[str(line.product_id.name)] += line.quantity
					else:
						invoiceQty.update({str(line.product_id.name):line.quantity})
			for line in sale.order_line:
				if orderLineQty.has_key(str(line.product_id.name)):
					orderLineQty[str(line.product_id.name)][0] += line.product_uom_qty
				else:
					orderLineQty.update({str(line.product_id.name):[line.product_uom_qty, line.product_id.default_code]})

			for stock in stocks:
				for line in stock.move_lines:
					if stockQty.has_key(str(line.product_id.name)):
						stockQty[str(line.product_id.name)] += line.product_uom_qty
					else:
						stockQty.update({str(line.product_id.name):line.product_uom_qty})

			for orderLine in orderLineQty:
				if stockQty.has_key(orderLine):
					quantityPending = stockQty[orderLine]
					if invoiceQty.has_key(orderLine):
						issuedQuan = invoiceQty[orderLine]
					else:
						issuedQuan = 0
					if quantityPending > 0:
						ws.write(count, 0, sale.partner_id.name, normal)
						ws.write(count, 1, sale.name, normal)
						ws.write(count, 2, date, normal)
						ws.write(count, 3, '['+str(orderLineQty[orderLine][1])+']'+str(orderLine), normal)
						ws.write(count, 4, orderLineQty[orderLine][0], normal)
						ws.write(count, 5, issuedQuan, normal)
						ws.write(count, 6, quantityPending, normal)
						count += 1
			invoiceQty = {}
			orderLineQty = {}
			stockQty = {}

		
sale_status_report('report.sale.status.report', 'sale.status.report', parser=sale_status_report_parser)
