from openerp import fields, api, models, _

class CancelStockPicking(models.TransientModel):

	_name = "stock.cancel"

	@api.multi
	def action_picking_cancel(self):

		stock_picking = self.env["stock.picking"].browse(self._context.get('active_ids'))
		if stock_picking:
			stock_picking.action_cancel()