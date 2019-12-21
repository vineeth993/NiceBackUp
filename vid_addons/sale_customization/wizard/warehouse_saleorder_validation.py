
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class WarehouseValidation(models.TransientModel):

	_name = "warehouse.validation"

	name = fields.Char(string="Order")
	order_date = fields.Date(string="Order Date")
	line_id = fields.One2many("warehouse.validation.line", "validation_id", string="Line")
	company_id = fields.Many2one("res.company", string="Company")

	@api.model
	def default_get(self, fields):
		res = super(WarehouseValidation, self).default_get(fields)
		order_id = self.env['sale.order'].browse(self._context.get('active_ids', []))
		if order_id:
			res['name'] = order_id.name
			res['order_date'] = order_id.date_order
			res['company_id'] = order_id.company_id.id
			items = []
			item = {}
			count = 0
			for line in order_id.order_line:
				count += 1
				prod_stock = line.product_id.with_context({'location':line.product_location.id}).qty_available				
				item = {
					'sl_no':count,
					'product_id':line.product_id.id,
					'product_qty':line.product_uom_qty,
					'location_id':line.product_location.id or line.product_id.product_tmpl_id.product_location.id,
					'product_stock':prod_stock if prod_stock > 0 else 0
					}
				items.append(item)
			res['line_id'] = items
		return res

	@api.multi
	def action_validate(self):
		order_id = self.env['sale.order'].browse(self._context.get('active_ids', []))
		for line in self.line_id:
			for order_line in order_id.order_line:
				if line.product_id == order_line.product_id and line.location_id != order_line.product_location:
					order_line.update({'product_location':line.location_id.id})

class WarehouseValidationLine(models.TransientModel):

	_name = "warehouse.validation.line"

	product_id = fields.Many2one("product.product", string="Product")
	product_qty = fields.Float(string="Quantity")
	location_id = fields.Many2one("stock.location", string="Warehouse")
	sl_no = fields.Integer("Sl No.")
	validation_id = fields.Many2one("warehouse.validation", string="Validation Ref")
	product_stock = fields.Float("Stock")

	@api.onchange("location_id")
	def onchange_location_id(self):
		for line in self:
			prod_stock = line.product_id.with_context({'location':line.location_id.id}).qty_available
			if prod_stock > 0:
				line.product_stock = prod_stock
			else:
				line.product_stock = 0
