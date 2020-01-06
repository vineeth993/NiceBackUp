import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
from openerp import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)

class sale_b2b_summary(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(sale_b2b_summary, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': dt,
            })
        self.context = context

class B2bSummary(report_xls):


    def b2b_sale_summary(self, invoice_obj, cr, uid, wb, data):

        report_name = 'B2B Sale Summary Report '
        ws = wb.add_sheet(report_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0
        cols = range(10)
        for col in cols:
            ws.col(col).width = 4000

        headers = {0:"GSTIN/UIN of Recipient", 1:"Reciever", 2:"Invoice Number", 3:'Invoice Date', 4:"Invoice Value", 5:'Place Of Supply', 6:'Reverse Charge', 7:'Applicable of Tax Rate' ,8:'Invoice Type', 9:'E-Commerce GSTIN', 10:'Rate', 11:'Taxable Value', 12:'Cess Amount'}

        for header in headers:
            ws.write(3, header, headers[header], self.title2)
        invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0]), ("sale_type_id", "=" , data['form']["type_id"][0])], order="id asc")
        invoices = invoice_obj.browse(cr, uid, invoice_id)

        total_invoice = 0
        total_inv_amt = 0
        total_taxable_amt = 0
        recipients = []
        count = 4
        for invoice in invoices:

            total_invoice += 1

            invoice_no = invoice.number.replace("SAJ-","")
            place_supply = str(invoice.partner_id.state_id.code) +'-'+ str(invoice.partner_id.state_id.name)
            add_disc = int(invoice.partner_id.adisc)
            sub_type = invoice.sale_sub_type_id.name
            taxes = {}
            tax_perc = 0
            taxable_value = 0

            if sub_type:
                if "Regular" in sub_type:
                   cust_type = 'Regular'
                elif "Deemed Export" in sub_type:
                    cust_type = "Deemed Exp"
                elif "SEZ Without" in sub_type:
                    cust_type = "SEZ supplies without payment"
                elif "SEZ With" in sub_type or "SEZ WIth" in sub_type :
                   cust_type = "SEZ supplies with payment"
            else:
                cust_type = 'False'

            if invoice.partner_id.gst_no not in recipients:
                recipients.append(invoice.partner_id.gst_no)

            for line in invoice.invoice_line:
                if line.invoice_line_tax_id:
                    if line.invoice_line_tax_id[0].gst_type in ["sgst", "cgst"]:
                        tax_perc = (line.invoice_line_tax_id[0].amount*2)*100
                    elif line.invoice_line_tax_id[0].gst_type in ["igst", "cess"]:
                        tax_perc = (line.invoice_line_tax_id[0].amount)*100
                else:
                    tax_perc = 0
                # if add_disc:
                #     taxable_value = line.price_subtotal - ((line.price_subtotal * add_disc)/100)
                # else:
                taxable_value = line.price_subtotal

                if taxes.has_key(tax_perc):
                    taxes[tax_perc] += round(taxable_value, 2)
                else:
                    taxes.update({tax_perc:round(taxable_value, 2)})

                total_taxable_amt += taxable_value
                date_invoice_obj = dt.strptime(str(invoice.date_invoice), '%Y-%m-%d')
                date_invoice = date_invoice_obj.strftime('%d-%b-%Y')
            for tax in sorted(taxes.iterkeys()):
                ws.write(count, 0, invoice.partner_id.gst_no, self.normal)
                ws.write(count, 1, invoice.partner_id.name, self.normal)
                ws.write(count, 2, invoice_no, self.normal)
                ws.write(count, 3, str(date_invoice), self.normal)
                ws.write(count, 4, invoice.round_off_total, self.number)
                ws.write(count, 5, place_supply, self.normal)
                ws.write(count, 6, 'N', self.normal)
                ws.write(count, 7, '', self.normal)
                ws.write(count, 8, cust_type, self.normal)
                ws.write(count, 9, '', self.normal)
                ws.write(count, 10, tax, self.number)
                ws.write(count, 11, taxes[tax], self.number)
                ws.write(count, 12, 0.0, self.number)
                count+=1
            
            total_inv_amt += invoice.round_off_total

        ws.write(0, 0 ,"Summary For B2B(4)", self.title2)
        headers = {0:"No of Recipients", 2:"No Of Invoices", 4:"Total Invoice Value", 11:'Total Taxable Value', 12:'Total Cess'}
        
        for header in headers:
            ws.write(1, header, headers[header], self.title2)

        ws.write(2, 0, len(recipients), self.number)
        ws.write(2, 2, total_invoice, self.number)
        ws.write(2, 4, total_inv_amt, self.number)
        ws.write(2, 11, total_taxable_amt, self.number)
        ws.write(2, 12, 0, self.number)


    def b2c_sale_summary(self, invoice_obj, cr, uid, wb, data):

        report_name_l = 'B2CL Sale Summary Report '
        wsl = wb.add_sheet(report_name_l)
        wsl.panes_frozen = True
        wsl.remove_splits = True
        wsl.portrait = 0  # Landscape
        wsl.fit_width_to_pages = 1
        row_pos = 0
    
        report_name_s = 'B2CS Sale Summary Report '
        wss = wb.add_sheet(report_name_s)
        wss.panes_frozen = True
        wss.remove_splits = True
        wss.portrait = 0  # Landscape
        wss.fit_width_to_pages = 1
        row_pos = 0
        cols = range(10)
        for col in cols:
            wss.col(col).width = 4000
            wsl.col(col).width = 4000

        headers_l = {0:"Invoice Number", 1:"Invoice date", 2:'Invoice Value', 3:"Place Of Supply", 4:'Rate', 5:'Taxable Value', 6:'Cess Amount', 7:'E-Commerce GSTIN'}
        headers_s = {0:"Type", 1:"Place Of Supply", 2:'Applicable of Tax Rate', 3:'Rate', 4:'Taxable Value', 5:'Cess Amount', 6:'E-Commerce GSTIN'}
        for header in headers_l:
            wsl.write(3, header, headers_l[header], self.title2)
        for header in headers_s:
            wss.write(3, header, headers_s[header], self.title2)
        invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0]), ("sale_type_id", "=" , data['form']["type_id"][0])],order="id asc")
        invoices = invoice_obj.browse(cr, uid, invoice_id)
        total_invoice_l, total_invoice_s = 0, 0
        total_inv_amt_l, total_inv_amt_s = 0, 0
        total_taxable_amt_l, total_taxable_amt_s = 0, 0
        count_l, count_s = 4, 4
        
        for invoice in invoices:

            invoice_no = invoice.number.replace("SAJ-","")
            place_supply = str(invoice.partner_id.state_id.code) +'-'+ str(invoice.partner_id.state_id.name)
            add_disc = int(invoice.partner_id.adisc)
            sub_type = invoice.sale_sub_type_id.name
            taxes = {}
            tax_perc = 0
            taxable_value = 0

            for line in invoice.invoice_line:
                if line.invoice_line_tax_id:
                    for tax_line in line.invoice_line_tax_id:
                        if tax_line.gst_type != 'cess':
                            if tax_line.gst_type in ["sgst", "cgst"]:
                                tax_perc = (tax_line.amount*2)*100
                            elif tax_line.gst_type == "igst":
                                tax_perc = (tax_line.amount)*100
                else:
                    tax_perc = 0
                if add_disc:
                    taxable_value = line.price_subtotal - ((line.price_subtotal * add_disc)/100)
                else:
                    taxable_value = line.price_subtotal

                if taxes.has_key(tax_perc):
                    taxes[tax_perc] += round(taxable_value, 2)
                else:
                    taxes.update({tax_perc:round(taxable_value, 2)})
            date_invoice_obj = dt.strptime(str(invoice.date_invoice), '%Y-%m-%d')
            date_invoice = date_invoice_obj.strftime('%d-%b-%Y')
            if invoice.round_off_total > 250000 and invoice.sale_sub_type_id.tax_categ == "igst":
                total_invoice_l += 1
                total_inv_amt_l += invoice.round_off_total
                for tax in taxes:
                    total_taxable_amt_l += taxes[tax]
                    wsl.write(count_l, 0, invoice.number.replace('SAJ-',''), self.normal)
                    wsl.write(count_l, 1, date_invoice, self.normal)
                    wsl.write(count_l, 2, invoice.round_off_total, self.number)
                    wsl.write(count_l, 3, place_supply, self.normal)
                    wsl.write(count_l, 4, tax, self.number)
                    wsl.write(count_l, 5, taxes[tax], self.number)
                    wsl.write(count_l, 6, 0, self.number)
                    count_l += 1
            else:
                for tax in taxes:
                    total_taxable_amt_s += taxes[tax]
                    wss.write(count_s, 0, "OE", self.normal)
                    wss.write(count_s, 1, place_supply, self.normal)
                    wss.write(count_s, 2, '', self.normal)
                    wss.write(count_s, 3, tax, self.number)
                    wss.write(count_s, 4, taxes[tax], self.number)
                    wss.write(count_s, 5, 0, self.number)
                    count_s += 1

        headers_l = {0:"No. of Invoices ", 2:'Total Invoice Value', 5:'Total Taxable Value', 6:'Total Cess'}
        headers_s = {4:'Total Taxable Value', 5:'Total Cess'}
        for header in headers_l:
            wsl.write(1, header, headers_l[header], self.title2)
        for header in headers_s:
            wss.write(1, header, headers_s[header], self.title2)

        wsl.write(0, 0 ,"Summary For B2CL(5)", self.title2)
        wss.write(0, 0 ,"Summary For B2CS(7)", self.title2)
        wsl.write(2, 0, total_invoice_l, self.number)
        wsl.write(2, 2, total_inv_amt_l, self.number)
        wsl.write(2, 5, total_taxable_amt_l, self.number)
        wsl.write(2, 6, 0, self.number)

        wss.write(2, 4, total_taxable_amt_s, self.number)
        wss.write(2, 5, 0, self.number)

    def exp_sale_summary(self, invoice_obj, cr, uid, wb, data):

        report_name = 'Exp Sale Summary Report '
        ws = wb.add_sheet(report_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0
        cols = range(10)
        for col in cols:
            ws.col(col).width = 4000

        headers = {0:"Export Type", 1:"Invoice Number", 2:"Invoice Date", 3:'Invoice Value', 4:"Port Code", 5:'Shipping Bill Number', 6:'Shipping Bill Date', 7:'Applicable of Tax Rate' ,8:'Rate', 9:'Taxable Value', 10:'Cess Amount'}

        for header in headers:
            ws.write(3, header, headers[header], self.title2)
        invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0]), ("sale_type_id", "=" , data['form']["type_id"][0])], order="id asc")
        invoices = invoice_obj.browse(cr, uid, invoice_id)

        total_invoice = 0
        total_inv_amt = 0
        total_taxable_amt = 0
        recipients = []
        count = 4
        for invoice in invoices:

            total_invoice += 1

            invoice_no = invoice.number.replace("SAJ-","")
            sub_type = invoice.sale_sub_type_id.name
            taxes = {}
            tax_perc = 0
            taxable_value = 0


            if sub_type:
                if "With Tax" in sub_type:
                    cust_type = "WPAY"
                elif "With Out Tax" in sub_type:
                    cust_type = "WOPAY"
        
            for line in invoice.invoice_line:
                if line.invoice_line_tax_id:
                    if line.invoice_line_tax_id[0].gst_type in ["sgst", "cgst"]:
                        tax_perc = (line.invoice_line_tax_id[0].amount*2)*100
                    elif line.invoice_line_tax_id[0].gst_type in ["igst", "cess"]:
                        tax_perc = (line.invoice_line_tax_id[0].amount)*100
                else:
                    tax_perc = 0

                taxable_value = line.price_subtotal

                if taxes.has_key(tax_perc):
                    taxes[tax_perc] += round(taxable_value, 2)
                else:
                    taxes.update({tax_perc:round(taxable_value, 2)})

                total_taxable_amt += taxable_value
                date_invoice_obj = dt.strptime(str(invoice.date_invoice), '%Y-%m-%d')
                date_invoice = date_invoice_obj.strftime('%d-%b-%Y')

            for tax in sorted(taxes.iterkeys()):
                ws.write(count, 0, cust_type, self.normal)
                ws.write(count, 1, invoice_no, self.normal)
                ws.write(count, 2, date_invoice, self.normal)
                ws.write(count, 3, invoice.round_off_total, self.number)
                ws.write(count, 4, '', self.normal)
                ws.write(count, 5, '', self.normal)
                ws.write(count, 6, '', self.normal)
                ws.write(count, 7, '', self.normal)
                ws.write(count, 8, tax, self.number)
                ws.write(count, 9, taxes[tax], self.number)
                ws.write(count, 10, 0.0, self.number)
                count+=1
            total_inv_amt += invoice.round_off_total

        ws.write(0, 0 ,"Summary For EXP(6)", self.title2)
        headers = {1:"No Of Invoices", 3:"Total Invoice Value", 5:'No. of Shipping Bill', 10:'Total Taxable Value'}
        
        for header in headers:
            ws.write(1, header, headers[header], self.title2)

        ws.write(2, 1, total_invoice, self.number)
        ws.write(2, 3, total_inv_amt, self.number)
        ws.write(2, 5, '', self.number )
        ws.write(2, 10, total_taxable_amt, self.number)

    def b2t_sale_summary(self, invoice_obj, cr, uid, wb, data):

        report_name = 'B2T Sale Summary Report '
        ws = wb.add_sheet(report_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0
        cols = range(10)
        for col in cols:
            ws.col(col).width = 4000

        headers = {0:"GSTIN/UIN of Recipient", 1:"Reciever", 2:"Invoice Number", 3:'Invoice Date', 4:"Invoice Value", 5:'Place Of Supply', 6:'Reverse Charge', 7:'Applicable of Tax Rate' ,8:'Invoice Type', 9:'E-Commerce GSTIN', 10:'Rate', 11:'Taxable Value', 12:'Cess Amount'}

        for header in headers:
            ws.write(3, header, headers[header], self.title2)
        invoice_id = invoice_obj.search(cr, uid, [('state','not in',('draft', 'cancel')), ("date_invoice", ">=", data['form']["from_date"]), ("date_invoice", "<=", data['form']['to_date']), ("company_id", "=", data['form']['company'][0]), ("sale_type_id", "=" , data['form']["type_id"][0])], order="id asc")
        invoices = invoice_obj.browse(cr, uid, invoice_id)

        total_invoice = 0
        total_inv_amt = 0
        total_taxable_amt = 0
        recipients = []
        count = 4
        for invoice in invoices:

            total_invoice += 1

            invoice_no = invoice.number.replace("SAJ-","")
            place_supply = str(invoice.partner_id.state_id.code) +'-'+ str(invoice.partner_id.state_id.name)
            add_disc = int(invoice.partner_id.adisc)
            sub_type = invoice.sale_sub_type_id.name
            taxes = {}
            tax_perc = 0
            taxable_value = 0

            if sub_type:
                if "Regular" in sub_type:
                   cust_type = 'Regular'
                elif "Deemed Export" in sub_type:
                    cust_type = "Deemed Exp"
                elif "SEZ Without" in sub_type:
                    cust_type = "SEZ supplies without payment"
                elif "SEZ With" in sub_type or "SEZ WIth" in sub_type :
                   cust_type = "SEZ supplies with payment"
            else:
                cust_type = 'False'

            if invoice.partner_id.gst_no not in recipients:
                recipients.append(invoice.partner_id.gst_no)

            for line in invoice.invoice_line:
                if line.invoice_line_tax_id:
                    if line.invoice_line_tax_id[0].gst_type in ["sgst", "cgst"]:
                        tax_perc = (line.invoice_line_tax_id[0].amount*2)*100
                    elif line.invoice_line_tax_id[0].gst_type in ["igst", "cess"]:
                        tax_perc = (line.invoice_line_tax_id[0].amount)*100
                else:
                    tax_perc = 0
                # if add_disc:
                #     taxable_value = line.price_subtotal - ((line.price_subtotal * add_disc)/100)
                # else:
                taxable_value = line.price_subtotal

                if taxes.has_key(tax_perc):
                    taxes[tax_perc] += round(taxable_value, 2)
                else:
                    taxes.update({tax_perc:round(taxable_value, 2)})

                total_taxable_amt += taxable_value
                date_invoice_obj = dt.strptime(str(invoice.date_invoice), '%Y-%m-%d')
                date_invoice = date_invoice_obj.strftime('%d-%b-%Y')
            for tax in sorted(taxes.iterkeys()):
                ws.write(count, 0, invoice.partner_id.gst_no, self.normal)
                ws.write(count, 1, invoice.partner_id.name, self.normal)
                ws.write(count, 2, invoice_no, self.normal)
                ws.write(count, 3, str(date_invoice), self.normal)
                ws.write(count, 4, invoice.round_off_total, self.number)
                ws.write(count, 5, place_supply, self.normal)
                ws.write(count, 6, 'N', self.normal)
                ws.write(count, 7, '', self.normal)
                ws.write(count, 8, cust_type, self.normal)
                ws.write(count, 9, '', self.normal)
                ws.write(count, 10, tax, self.number)
                ws.write(count, 11, taxes[tax], self.number)
                ws.write(count, 12, 0.0, self.number)
                count+=1
            
            total_inv_amt += invoice.round_off_total

        ws.write(0, 0 ,"Summary For B2T", self.title2)
        headers = {0:"No of Recipients", 2:"No Of Invoices", 4:"Total Invoice Value", 11:'Total Taxable Value', 12:'Total Cess'}
        
        for header in headers:
            ws.write(1, header, headers[header], self.title2)

        ws.write(2, 0, len(recipients), self.number)
        ws.write(2, 2, total_invoice, self.number)
        ws.write(2, 4, total_inv_amt, self.number)
        ws.write(2, 11, total_taxable_amt, self.number)
        ws.write(2, 12, 0, self.number)

    def generate_xls_report(self, parser, xls_styles, data, objects, wb):

        cr, uid = self.cr, self.uid
        self.title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
        self.normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
        self.number          = xlwt.easyxf(num_format_str='#,##0;(#,##0)')
        self.number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        self.number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')
        
        invoice_obj = self.pool.get("account.invoice")
        if "B2B" in data['form']["type_id"][1]:
            self.b2b_sale_summary(invoice_obj, cr, uid, wb, data)
        elif "B2C" in data['form']["type_id"][1]:
            self.b2c_sale_summary(invoice_obj, cr, uid, wb, data)
        elif "EXP" in data['form']["type_id"][1]:
            self.exp_sale_summary(invoice_obj, cr, uid, wb, data)
        elif "B2T" in data['form']["type_id"][1]:
            self.b2t_sale_summary(invoice_obj, cr, uid, wb, data)

B2bSummary('report.gstr.b2b_report', "gstr.b2b_report", parser=sale_b2b_summary)
