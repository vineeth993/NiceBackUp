import time 
from openerp import api, models
import logging

_logger = logging.getLogger(__name__)

class ReportLr(models.AbstractModel):

	_name = "report.lr_doc.report_lr_doc"

	@api.model
	def render_html(self, docids, data=None):
		
		tax_lines_taxable = {'0.0':{}, '5.0': {}, '12.0': {}, '18.0': {}, '28.0': {}}
		tax_lines_total = {'0.0':{}, '5.0': {}, '12.0': {}, '18.0': {}, '28.0': {}}
		doc_id = self.env["lr.doc"].browse(data["doc_id"])
		taxable_amount = 0
		hsn_temp = []
		invoice_hsn_values = {}
		hsn_particulars = {}
		for inv_id in data:
			hsn_particulars = {}
			hsn_temp = []
			if inv_id != "doc_id":
				inv_obj = self.env['account.invoice'].browse(data[inv_id])
				for invoice_line in inv_obj.invoice_line:
					tax_percnt = 0.0
					total_amount = 0.0
					if invoice_line.invoice_line_tax_id:
						if invoice_line.invoice_line_tax_id[0].gst_type == "sgst" or invoice_line.invoice_line_tax_id[0].gst_type == "cgst":
							tax_percnt = (invoice_line.invoice_line_tax_id[0].amount * 2)*100
						elif invoice_line.invoice_line_tax_id[0].gst_type == "igst":
							tax_percnt = (invoice_line.invoice_line_tax_id[0].amount)*100
					else:
						tax_percnt = 0.0
					total_amount = round(invoice_line.price_subtotal + ((invoice_line.price_subtotal *tax_percnt)/100))

					if tax_lines_taxable[str(tax_percnt)].has_key(inv_obj.number):
						tax_lines_taxable[str(tax_percnt)][inv_obj.number] += round(invoice_line.price_subtotal, 2)
					else:
						tax_lines_taxable[str(tax_percnt)].update({inv_obj.number: round(invoice_line.price_subtotal, 2)})

					if tax_lines_total[str(tax_percnt)].has_key(inv_obj.number):
						tax_lines_total[str(tax_percnt)][inv_obj.number] += round(total_amount, 2)
					else:
						tax_lines_total[str(tax_percnt)].update({inv_obj.number: round(total_amount, 2)})
					if invoice_line.product_id.hs_code_id.code[0:2]	in hsn_temp:
						continue
					hsn_temp.append(invoice_line.product_id.hs_code_id.code[0:2])
				taxable_amount += inv_obj.amount_untaxed

				for hsn in hsn_temp:
					for invoice_line in inv_obj.invoice_line:
						hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total = 0, 0, 0, 0
						hsn_total_taxablevalue = 0
						tax_percnt = 0
						if hsn != invoice_line.product_id.hs_code_id.code[0:2]:
							continue
						hsn_total_taxablevalue += invoice_line.price_subtotal
						for tax in invoice_line.invoice_line_tax_id:
							if tax.gst_type == "cgst":
								hsn_cgst_total += round((invoice_line.price_subtotal * tax.amount), 2)
							elif tax.gst_type == "sgst":
								tax_percnt = (tax.amount * 2)*100
								hsn_sgst_total = round((invoice_line.price_subtotal * tax.amount), 2)
							elif tax.gst_type == "igst":
								tax_percnt = (tax.amount)*100
								hsn_igst_total = round((invoice_line.price_subtotal * tax.amount), 2)
							elif tax.gst_type == "cess":
								hsn_cess_total = round((invoice_line.price_subtotal * tax.amount), 2)
						if not hsn_particulars.has_key(hsn):
							hsn_particulars.update({hsn:{round(tax_percnt, 2):[round(hsn_total_taxablevalue, 2), round(hsn_igst_total, 2), round(hsn_sgst_total, 2), round(hsn_cgst_total, 2), round(hsn_cess_total, 2)]}})
						else:
							if not hsn_particulars[hsn].has_key(round(tax_percnt, 2)):
								hsn_particulars[hsn].update({round(tax_percnt, 2):[round(hsn_total_taxablevalue, 2), round(hsn_igst_total, 2), round(hsn_sgst_total, 2), round(hsn_cgst_total, 2), round(hsn_cess_total, 2)]})
							else:
								hsn_particulars[hsn][round(tax_percnt, 2)][0] += round(hsn_total_taxablevalue, 2)
								hsn_particulars[hsn][round(tax_percnt, 2)][1] += round(hsn_igst_total, 2)
								hsn_particulars[hsn][round(tax_percnt, 2)][2] += round(hsn_sgst_total, 2)
								hsn_particulars[hsn][round(tax_percnt, 2)][3] += round(hsn_cgst_total, 2)
								hsn_particulars[hsn][round(tax_percnt, 2)][4] += round(hsn_cess_total, 2)

				if not invoice_hsn_values.has_key(inv_obj.number):
					invoice_hsn_values.update({inv_obj.number:hsn_particulars})
		docargs = {
			"doc_id": docids,
			"docs": doc_id,
			"doc_model":'lr.doc',
			"taxes_taxable" : tax_lines_taxable,
			"taxes_total" : tax_lines_total,
			"taxable_amount": taxable_amount,
			"invoice_hsn_values":invoice_hsn_values
		}
		return self.env['report'].render('lr_doc.report_lr_doc', docargs)