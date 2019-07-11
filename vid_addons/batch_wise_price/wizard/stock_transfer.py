from openerp import fields, api, models, _
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockTransferDetails(models.TransientModel):

	_inherit = 'stock.transfer_details'

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		res = super(StockTransferDetails, self).default_get(cr, uid, fields, context=context)
		picking_ids = context.get('active_ids', [])
		active_model = context.get('active_model')

		if not picking_ids or len(picking_ids) != 1:
			# Partial Picking Processing may only be done for one picking at a time
			return res
		assert active_model in ('stock.picking'), 'Bad context propagation'
		picking_id, = picking_ids
		picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
		items = []
		packs = []
		if not picking.pack_operation_ids:
			picking.do_prepare_partial()
		for op in picking.pack_operation_ids:
			price_list = None
			if op.lot_id.pricelist:
				price_list =  op.lot_id.pricelist.id
			# else:
			# 	get_pricelist = self.pool.get('product.batch.pricelist').search(cr, uid, [('price_ids.product_id', '=', op.product_id.id)], context=context)
			# 	if get_pricelist:
			# 		value = min(get_pricelist)
			# 		price_list = value
			
			item = {
				'packop_id': op.id,
				'product_id': op.product_id.id,
				'product_uom_id': op.product_uom_id.id,
				'quantity': op.product_qty,
				'package_id': op.package_id.id,
				'lot_id': op.lot_id.id,
				'pricelist_id':price_list,
				'sourceloc_id': op.location_id.id,
				'destinationloc_id': op.location_dest_id.id,
				'result_package_id': op.result_package_id.id,
				'date': op.date, 
				'owner_id': op.owner_id.id,
			}
			if op.product_id:
				items.append(item)
			elif op.package_id:
				packs.append(item)
		res.update(item_ids=items)
		res.update(packop_ids=packs)
		return res

class StockTransfer(models.TransientModel):

	_inherit = 'stock.transfer_details_items'

	pricelist_id = fields.Many2one("product.batch.pricelist", string="Year Wise Price", readonly="True")

	@api.onchange('lot_id')
	def onchange_lot_id(self):
		if self.lot_id.pricelist:
			self.pricelist_id = self.lot_id.pricelist.id




