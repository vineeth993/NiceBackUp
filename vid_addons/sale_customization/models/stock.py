# -*- coding: utf-8 -*-

from openerp.tools.float_utils import float_compare, float_round
from openerp.osv import fields, osv
import datetime
import logging
from openerp import api

_logger = logging.getLogger(__name__)

class stock_picking(osv.osv):
	_inherit = 'stock.picking'

	def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
		if context is None:
			context = {}
		partner, currency_id, company_id, user_id = key
		strtoDate = datetime.datetime.strptime(move.picking_id.sale_id.date_order, '%Y-%m-%d %I:%M:%S')
		sale_order = move.picking_id.sale_id.name+'-'+datetime.datetime.strftime(strtoDate, '%d/%m/%y')
		if inv_type in ('out_invoice', 'out_refund'):
			account_id = partner.property_account_receivable.id
			payment_term = partner.property_payment_term.id or False
		else:
			account_id = partner.property_account_payable.id
			payment_term = partner.property_supplier_payment_term.id or False
		warehouse_id = self.pool.get("stock.location").get_warehouse(cr, uid, move.picking_id.picking_type_id.default_location_src_id)
		return {
			'origin': move.picking_id.name,
			'date_invoice': context.get('date_inv', False),
			'user_id': user_id,
			'section_id':move.picking_id.sale_id.section_id.id,
			'partner_id': partner.id,
			'account_id': account_id,
			'payment_term': payment_term,
			'type': inv_type,
			'fiscal_position': partner.property_account_position.id,
			'company_id': company_id,
			'currency_id': currency_id,
			'journal_id': journal_id,
			'partner_selling_type':move.picking_id.sale_id.partner_selling_type,
			'normal_disc':move.picking_id.sale_id.normal_disc,
			'extra_discount':move.picking_id.sale_id.extra_discount,
			'nonread_extra_disocunt':move.picking_id.sale_id.nonread_extra_disocunt,
			'nonread_normal_disocunt':move.picking_id.sale_id.nonread_normal_disocunt,
			'sale_order':sale_order,
			'comment':move.picking_id.sale_id.note,
			'partner_shipping_id':move.picking_id.sale_id.partner_shipping_id.id,
			'brand_id':move.picking_id.sale_id.brand_id.id,
			'warehouse_id':warehouse_id
		}
	@api.cr_uid_ids_context
	def do_transfer(self, cr, uid, picking_ids, context=None):
		"""
			If no pack operation, we do simple action_done of the picking
			Otherwise, do the pack operations
		"""
		if not context:
			context = {}
		notrack_context = dict(context, mail_notrack=True)
		stock_move_obj = self.pool.get('stock.move')
		for picking in self.browse(cr, uid, picking_ids, context=context):
			if not picking.pack_operation_ids:
				self.action_done(cr, uid, [picking.id], context=context)
				continue
			else:
				need_rereserve, all_op_processed = self.picking_recompute_remaining_quantities(cr, uid, picking, context=context)
				#create extra moves in the picking (unexpected product moves coming from pack operations)
				todo_move_ids = []
				if not all_op_processed:
					todo_move_ids += self._create_extra_moves(cr, uid, picking, context=context)

				#split move lines if needed
				toassign_move_ids = []
				for move in picking.move_lines:
					remaining_qty = move.remaining_qty
					if move.state in ('done', 'cancel'):
						#ignore stock moves cancelled or already done
						continue
					elif move.state == 'draft':
						toassign_move_ids.append(move.id)
					if float_compare(remaining_qty, 0,  precision_rounding = move.product_id.uom_id.rounding) == 0:
						if move.state in ('draft', 'assigned', 'confirmed'):
							todo_move_ids.append(move.id)
					elif float_compare(remaining_qty,0, precision_rounding = move.product_id.uom_id.rounding) > 0 and \
								float_compare(remaining_qty, move.product_qty, precision_rounding = move.product_id.uom_id.rounding) < 0:
						new_move = stock_move_obj.split(cr, uid, move, remaining_qty, context=notrack_context)
						todo_move_ids.append(move.id)
						#Assign move as it was assigned before
						toassign_move_ids.append(new_move)
				if need_rereserve or not all_op_processed: 
					if not picking.location_id.usage in ("supplier", "production", "inventory"):
						self.rereserve_quants(cr, uid, picking, move_ids=todo_move_ids, context=context)
					self.do_recompute_remaining_quantities(cr, uid, [picking.id], context=context)
				if todo_move_ids and not context.get('do_only_split'):
					self.pool.get('stock.move').action_done(cr, uid, todo_move_ids, context=notrack_context)
				elif context.get('do_only_split'):
					context = dict(context, split=todo_move_ids)
			backorder_id = self._create_backorder(cr, uid, picking, context=context)
			if toassign_move_ids:
				stock_move_obj.action_assign(cr, uid, toassign_move_ids, context=context)
			picking_obj = self.pool.get("stock.picking")
			picking_id = picking_obj.browse(cr, uid, backorder_id)

			if picking_id:
				if picking_id.state not in ('done', 'cancel'):
					self.do_unreserve(cr, uid, picking_id.id, context=context)
		return True

class stock_move(osv.osv):

	_inherit = "stock.move"
	_order = 'name, product_id, date_expected desc, id'

	def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
		res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
		if inv_type in ('out_invoice', 'out_refund') and move.procurement_id and move.procurement_id.sale_line_id:
			sale_line = move.procurement_id.sale_line_id
			res['additional_discount'] = sale_line.additional_discount
		return res

