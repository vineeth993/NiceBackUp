from openerp import fields, api, models, _

class GstrConsolidated(models.TransientModel):

	_name = "gstr.consolidated"
	
	from_date = fields.Date("From date")
	to_date = fields.Date("To Date")
	company = fields.Many2one("res.company", string="Company", default=lambda self: self.env['res.users']._get_company())

	@api.multi
	def action_print(self):

		data = {}
		data["id"] = self.id
		data["form"] = self.read()[0]
		name = str(self.company.name) +" Consolidated Report"
		return{
			'type':'ir.actions.report.xml',
			'report_name':'gstr.consolidated',
			'datas':data,
			'name':name
		}