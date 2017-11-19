from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)

class B2BReport(models.TransientModel):
	
	_name = "gstr.b2b_report"

	from_date = fields.Date("From date")
	to_date = fields.Date("To Date")
	company = fields.Many2one("res.company", string="Company", default=lambda self: self.env['res.users']._get_company())
	type_id = fields.Many2one("sale.order.type", string="Sale Type")

	@api.multi
	def print_b2b_report(self):
		data = {}
		data["id"] = self.id
		data["form"] = self.read()[0]
		_logger.info("Testing = "+str(data))
		return {
    		"type":"ir.actions.report.xml",
    		"report_name":"gstr.b2b_report",
    		"datas":data
    	}

