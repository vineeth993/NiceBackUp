
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockTranser(models.TransientModel):

	_inherit = "stock.transfer_details_items"

	@api.onchange("lot_id", "quantity")
	def onchange_lot_id(self):

		stock_picking = self.env['stock.picking'].browse(self._context.get('stock_picking'))
		if self.lot_id and self.quantity and not stock_picking.is_dc:
			qty_available = self.product_id.with_context({'location':self.sourceloc_id.id, 'lot_id':self.lot_id.id}).qty_available
			if qty_available <= 0:
				raise ValidationError("There is no enough quantity against the given batch number")
			elif qty_available < self.quantity:
				message = 'Availble quantity for this batch %d units, the quantity needed to execute %d units have been changed to %d units'%(qty_available, self.quantity, qty_available)
				self.quantity = qty_available
				return{
					'warning': {'title': _('Warning'), 'message': _(message),}
				}	
