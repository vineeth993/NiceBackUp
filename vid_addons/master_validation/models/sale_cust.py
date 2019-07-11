from openerp import models, api, fields, _
from openerp.exceptions import ValidationError

class SaleCust(models.Model):

	_inherit = "sale.order"

	@api.multi
	def action_button_confirm(self):
		if self.partner_id.state != "approve":
			raise ValidationError("Please approve the given partner before proceeding")
		return super(SaleCust, self).action_button_confirm()