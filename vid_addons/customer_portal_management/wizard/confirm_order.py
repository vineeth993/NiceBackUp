
from openerp import fields, models, api, _

class PortalSaleConfrim(models.TransientModel):

	_name = "portal.sale.confirm"

	@api.multi
	def confirm_sale(self):
		
		customer_order = self.env['portal.sale'].browse(self._context.get('active_ids', []))
		if customer_order:
			customer_order.action_confirm()
		