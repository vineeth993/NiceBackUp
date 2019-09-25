
from openerp import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class cess_sale_report(models.TransientModel):

	_name = "cess_sale.report"
	
	from_date = fields.Date("From date")
	to_date = fields.Date("To Date")
	sale_sub_type = fields.Many2one("sale.order.sub.type", string="Sub Type")
	sale_order_type = fields.Many2one("sale.order.type", string="Sale Order Type")
	company_id = fields.Many2one("res.company", string="Company", default=lambda self:self.env.user.company_id.id)

	@api.multi
	def action_cess_report(self):

		data = {}
		data["id"] = self.id
		data["form"] = self.read()[0]
		name = str(self.company_id.name) + 'Cess'

		return {
    		"type":"ir.actions.report.xml",
    		"report_name":"cess_sale.report",
    		"datas":data,
    		"name":name
    	}



