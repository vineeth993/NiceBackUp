from openerp import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)

class SaleReport(models.Model):

	_inherit = "sale.order.line"

	def get_product_qty(self, product, warehouse_id):

		available_qty = product.with_context({'warehouse':warehouse_id.id}).qty_available
		return available_qty