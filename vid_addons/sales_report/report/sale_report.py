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

    def customer_pending_report(self, parser, xls_styles, data, objects, wb):

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
                ('date_order', '>=', data['form']['date_from']), ('date_order', '<=', data['form']['date_to']),("partner_id", "=", int(data['form']['customer'][0]))
                ])
        count = 3
        

        sales = sale_obj.browse(cr, uid, sale_ids)
        ws.write(0, 3, "Pending Sale Order For "+str(data['form']['customer'][1]), title2)

        headers = {
            0: 'SO DATE', 1: 'SO NUMBER', 2: 'Product', 3:'Normal Disc', 4:'Additional Disc', 5:'Extra Disc',6: 'Total Quantity', 7: 'ISSUED QTY', 8: 'Pending Quantity',
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

            for line in stocks.move_lines:
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
                        ws.write(count, 0, date, normal)
                        ws.write(count, 1, sale.name, normal)
                        ws.write(count, 2, '['+str(orderLineQty[orderLine][4])+']'+str(orderLine), normal)
                        ws.write(count, 3, orderLineQty[orderLine][1], normal)
                        ws.write(count, 4, orderLineQty[orderLine][2], normal)
                        ws.write(count, 5, orderLineQty[orderLine][3], normal)
                        ws.write(count, 6, orderLineQty[orderLine][0], normal)
                        ws.write(count, 7, issuedQuan, normal)
                        ws.write(count, 8, quantityPending, normal)
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
        ws.write(0, 3, "Pending Sale Order For "+str(data['form']['product'][1]), title2)

        headers = {
            0: 'Partner', 1: 'Sale Order', 2: 'date', 3: 'Total Quantity', 4: 'ISSUED QTY', 5: 'Pending Quantity',
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
                    orderLineQty[sale.partner_id.name][0] += line.product_uom_qty
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
                    issuedQuan = orderLineQty[order] - invoiceQty[order]
                else:
                    issuedQuan = 0
                if issuedQuan >= 0:
                    ws.write(count, 0, order, normal)
                    ws.write(count, 1, sale.name, normal)
                    ws.write(count, 2, date, normal)
                    ws.write(count, 3, orderLineQty[order], normal)
                    ws.write(count, 4, issuedQuan, normal)
                    ws.write(count, 5, (orderLineQty[order] - issuedQuan), normal)
                    count += 1
            
            orderLineQty = {}
            invoiceQty = {}        

sale_status_report('report.sale.status.report', 'sale.status.report', parser=sale_status_report_parser)
