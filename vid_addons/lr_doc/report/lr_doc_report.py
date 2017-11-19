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
		for inv_id in data:
			if inv_id != "doc_id":
				inv_obj = self.env['account.invoice'].browse(data[inv_id])
				for invoice_line in inv_obj.invoice_line:
					tax_percnt = 0.0
					total_amount = 0.0
					if invoice_line.invoice_line_tax_id[0]:
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

		_logger.info("Tax Lines are = "+str(doc_id))
		docargs = {
			"doc_id": docids,
			"docs": doc_id,
			"doc_model":'lr.doc',
			"taxes_taxable" : tax_lines_taxable,
			"taxes_total" : tax_lines_total
		}
		return self.env['report'].render('lr_doc.report_lr_doc', docargs)