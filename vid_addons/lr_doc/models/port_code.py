from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


class port_code(models.Model):

	_name = "port.code"

	name = fields.Char(string="Code", required=1)
	location = fields.Char(string="Location", required=1)
	state_id = fields.Many2one("res.country.state",string="state")
	country_id = fields.Many2one("res.country", string="Country",store=True)

	@api.one
	@api.constrains("name")
	def name_validation(self):
		if self.name:
			value =self.search([("name","=", self.name)])
			if len(value) > 1:
				raise ValidationError("Port Code Already Exists ")

	@api.onchange("state_id")
	def onchange_state_id(self):
		self.country_id = self.state_id.country_id

