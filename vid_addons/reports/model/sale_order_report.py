from openerp import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)

class SaleReport(models.Model):

	_inherit = "sale.order.line"

	def get_product_qty(self, product, warehouse_id):

		available_qty = product.with_context({'warehouse':warehouse_id.id}).qty_available
		return available_qty

class StockMove(models.Model):

	_inherit = "stock.move"

	def get_available(self, product_id, location_id):

		qty_available = product_id.with_context({'warehouse':location_id.warehouse_id.id}).qty_available
		return qty_available

