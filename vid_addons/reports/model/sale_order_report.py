from openerp import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)

class SaleReport(models.Model):

	_inherit = "sale.order.line"

	def get_product_qty(self, product, warehouse_id):

		available_qty = product.with_context({'warehouse':warehouse_id.id}).qty_available
		return available_qty

	def get_all_qty(self, product, company_id):

		stocks = ""

		locations = self.env['stock.location'].search([('company_id', '=', company_id.id), ('type', '=', 'finished')])
		for location in locations:
			location_stock = product.with_context({'location':location.id}).qty_available
			if location_stock > 0:
				stocks += location.location_id.name + '-' + str(location_stock) + ' : '
		return stocks

class StockMove(models.Model):

	_inherit = "stock.move"

	def get_available(self, product_id, location_id):

		qty_available = product_id.with_context({'location':location_id.id}).qty_available
		return qty_available

