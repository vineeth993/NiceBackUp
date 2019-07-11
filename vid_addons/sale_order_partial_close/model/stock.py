from openerp import api, fields, models
from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.float_utils import float_compare, float_round

import logging

_logger = logging.getLogger(__name__)

class stock(osv.osv):
	_inherit = "stock.picking"

	@api.cr_uid_ids_context
	def do_transfer_cancel(self, cr, uid, picking_ids, context=None):
	    """
	        If no pack operation, we do simple action_done of the picking
	        Otherwise, do the pack operations
	    """
	    if not context:
	    	context = {}
	    notrack_context = dict(context, mail_notrack=True)
	    stock_move_obj = self.pool.get('stock.move')
	    backorder = None
	    for picking in self.browse(cr, uid, picking_ids, context=context):
	        if not picking.pack_operation_ids:
	            self.action_cancel(cr, uid, [picking.id], context=context)
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
	                self.pool.get('stock.move').action_cancel(cr, uid, todo_move_ids, context=notrack_context)
	            elif context.get('do_only_split'):
	                context = dict(context, split=todo_move_ids)
	        backorder =  self._create_backorder(cr, uid, picking, context=context)
	        if toassign_move_ids:
	        	_logger.info("To assign move ids ="+str(toassign_move_ids))
	        	stock_move_obj.action_assign(cr, uid, toassign_move_ids, context=context)
	    return backorder
