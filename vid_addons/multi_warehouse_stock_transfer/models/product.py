
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):

	_inherit = "product.template"

	def action_view_dc(self, cr, uid, ids, context=None):

		act_obj = self.pool.get('ir.actions.act_window')
		mod_obj = self.pool.get('ir.model.data')
		product_ids = []
		for template in self.browse(cr, uid, ids, context=context):
			product_ids += [x.id for x in template.product_variant_ids]
		result = mod_obj.xmlid_to_res_id(cr, uid, 'multi_warehouse_stock_transfer.dc_line_product_view',raise_if_not_found=True)
		result = act_obj.read(cr, uid, [result], context=context)[0]
		result['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "]), ('state', '=', 'done')]"
		return result
