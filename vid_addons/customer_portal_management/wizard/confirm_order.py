
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

class PortalSaleConfrim(models.TransientModel):

	_name = "portal.sale.confirm"

	@api.multi
	def confirm_sale(self):
		
		customer_order = self.env['portal.sale'].browse(self._context.get('active_ids'))
		if not customer_order.line_id:
			raise ValidationError("Please input product to purchase")
		if customer_order:
			customer_order.action_confirm()
		
