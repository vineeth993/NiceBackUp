from openerp import fields, models, api, _
import logging
from datetime import date
import datetime

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):

	_inherit = "stock.picking"

	outward_id = fields.Many2one("multi.stock.outward", string="Outward Ref", copy=True)
	inward_id = fields.Many2one("multi.stock.transfer", string="Inward Ref", copy=True)

class StockMove(models.Model):

	_inherit = "stock.move"

	outward_line_id = fields.Many2one("multi.stock.outward.line",string="Transfer line")

	def action_done(self, cr, uid, ids, context=None):
		res = super(StockMove, self).action_done(cr, uid, ids, context=context)
		for move in self.browse(cr, uid, ids, context=context):
			if move.outward_line_id:
				quant = move.product_uom_qty
				move.outward_line_id.issued_quant += quant
				move.outward_line_id.state = 'issue'
				move.outward_line_id.transfer_id.state = 'issue'
				move.outward_line_id.transfer_id.quant_issued_date = date.today()
		return res