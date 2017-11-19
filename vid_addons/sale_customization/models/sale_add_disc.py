from openerp.osv import fields, osv
from openerp import api
import openerp.addons.decimal_precision as dp
import logging 

_logger = logging.getLogger(__name__)

class SaleOrderLine(osv.osv):

	_inherit = "sale.order.line"

	def _calc_line_base_price(self, cr, uid, line, context=None):
	 	price_unit_normal = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
	 	if line.extra_discount:
	 		price_unit_normal = price_unit_normal * (1 - (line.extra_discount or 0.0) / 100.0)
	 	if line.additional_discount:
	 		price_unit_normal = price_unit_normal * (1 - (line.additional_discount or 0.0) / 100.0)
	 	return price_unit_normal

	def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		res = {}
		total = 0.0
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			price = self._calc_line_base_price(cr, uid, line, context=context)
			qty = self._calc_line_quantity(cr, uid, line, context=context)
			taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, qty,
                                        line.product_id,
                                        line.order_id.partner_id)
			cur = line.order_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
		return res

	_columns = {
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'))
	}