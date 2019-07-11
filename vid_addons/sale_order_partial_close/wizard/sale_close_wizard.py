from openerp import api, fields, models
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class sale_close(models.TransientModel):
	_name = "sale.partial.close"

	order_id = fields.Many2one("sale.order", string="Sale Order", domain=[("state", "in", ("progress", "shipping_except"))])
	line_id = fields.One2many("sale.partial.line", "close_id", string="refernce")

	@api.onchange("order_id")
	def get_partial_prod(self):
		if self.order_id:
			stock_object = self.env["stock.picking"].search([('origin', '=', self.order_id.name), ('state', 'not in', ('cancel', 'done'))])
			if stock_object:
				if not stock_object.pack_operation_ids:
					stock_object.force_assign()
					stock_object.do_prepare_partial()
				# stock_move = self.env["stock.move"].search([("picking_id", "=", stock_object.id)])
				value = [(0, 0 , {'product_id':line.product_id, 'quantity':line.product_qty, 'packop_id':line.id})for line in stock_object.pack_operation_ids]
				self.line_id = value
		
	@api.multi
	def process_cancel(self):
		stock_object = self.env["stock.picking"].search([('origin', '=', self.order_id.name), ('state', 'not in', ('cancel', 'done'))])
		stock_move = self.env["stock.move"].search([("picking_id", "=", stock_object.id)])
		packing_ids = []
		value = {}
		backorder = None
		stock_quantity = {line.product_id:[line.product_uom_qty, line.product_uom, line.location_dest_id, line.location_id, line.date] for line in stock_move} 
		for line in self.line_id: 
			if line.close or stock_quantity[line.product_id][0] > line.quantity:
				value = {
						'product_uom_id':stock_quantity[line.product_id][1].id,
						'product_id':line.product_id.id,
						'product_qty':line.quantity,
						'location_dest_id':stock_quantity[line.product_id][2].id,
						'location_id':stock_quantity[line.product_id][3].id,
						'date':stock_quantity[line.product_id][4] if stock_quantity[line.product_id][4] else datetime.now(),
						'owner_id':stock_object.owner_id.id,
					}
				if line.packop_id:
					_logger.info("pack op id = "+str(value))
					line.packop_id.with_context(no_recompute=True).write(value)
					packing_ids.append(line.packop_id.id)
				else:
					value['picking_id'] = stock_object.id,
					packing_id = self.env['stock.pack.operation'].create(value)
					packing_ids.append(packing_id.id)
		if packing_ids:
			packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', stock_object.id), '!', ('id', 'in', packing_ids)])
			packops.unlink()
			backorder = stock_object.do_transfer_cancel()
			self.order_id.delete_workflow()
			if backorder:
				self.order_id.state = "progress"
			else:
				self.order_id.state = "done"

		return True

class sale_close_line(models.TransientModel):
	_name = "sale.partial.line"

	product_id = fields.Many2one("product.product", string="Product")
	quantity = fields.Float(string="Quantity")
	close = fields.Boolean(string="Close")
	close_id = fields.Many2one("sale.partial.close", string="Reference")
	packop_id = fields.Many2one('stock.pack.operation', 'Operation')