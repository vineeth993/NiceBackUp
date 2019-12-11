
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):

	_inherit = "stock.picking"

	issue_id = fields.Many2one("warehouse.stock.issue", string="Issue")
	request_id = fields.Many2one("warehouse.stock.request", string="Request")
	is_dc = fields.Boolean(string="DC", default=False)
	warehouse_dc_id = fields.Many2one('dc.warehouse', string="Dc")
	location_type = fields.Selection([('raw', 'Raw Materials'),
										('manufacture', 'Manufacturing'),
										('semi-finished', 'Semi Finished'),
										('finished', 'Finished'),
										], string='Type', compute="_get_location")
	sale_bill_type = fields.Selection([('normal', 'Normal'), ('special', 'Special'), ('extra', 'Extra')], string="Bill Type", compute="_get_values")
	normal_discount = fields.Float("Normal Disc", compute="_get_values")
	extra_discount = fields.Float("Extra Disc", compute="_get_values")

	@api.depends()
	def _get_values(self):
		for picking in self:
			if picking.group_id:
				sale_ids = self.env['sale.order'].search([('procurement_group_id', '=', picking.group_id.id)])
				if sale_ids:
					picking.sale_bill_type = sale_ids[0].partner_selling_type
					if sale_ids[0].partner_selling_type == "normal":
						picking.normal_discount = sale_ids[0].normal_disc
						picking.extra_discount = sale_ids[0].extra_discount
					elif sale_ids[0].partner_selling_type == "extra":
						picking.normal_discount = sale_ids[0].normal_disc
						picking.extra_discount = sale_ids[0].nonread_extra_disocunt
					else:
						picking.normal_discount = sale_ids[0].nonread_normal_disocunt
						picking.extra_discount = sale_ids[0].nonread_extra_disocunt						
					# res[picking.id] = sale_ids[0].partner_selling_type

	@api.depends()
	def _get_location(self):
		for res in self:
			res.location_type = res.location_id.type

	@api.multi
	def action_create_dc(self):
		
		dc_id = self.create_dc()
		self.write({'warehouse_dc_id':dc_id.id})
		view_id = self.env.ref('multi_warehouse_stock_transfer.warehouse_dc_form')

		if dc_id:
			action =  {
				'name':'Warehouse DC',
				'view_type':'form',
				'view_mode':'form',
				'res_model':'dc.warehouse',
				'view_id':view_id.id,
				'type':'ir.actions.act_window',
				'res_id': dc_id.id,
				'domain':[('id','=',dc_id.id)],
				'target':'current',
			}
			return action

	def create_dc(self):
		
		dc_obj = self.env["dc.warehouse"]
		dc_line_obj = self.env["dc.warehouse.line"]
		if not self.warehouse_dc_id:
			dc_val = {
				'request_warehouse_from_id':self.issue_id.request_warehouse_from_id.id,
				'partner_id':self.issue_id.partner_id.id,
				'warehouse_id':self.issue_id.warehouse_id.id,
				'company_id':self.company_id.id,
				'request_date':self.issue_id.request_date,
				'issue_refernce':self.issue_id.id,
				'reference':self.issue_id.reference.id,
				'currency_id':self.issue_id.currency_id.id,
			}

			dc_id = dc_obj.create(dc_val)

			for move in self.move_lines:
				if move:
					for quant in move.quant_ids:
						if quant.qty > 0:
							dc_line_val = {
								'product_id':quant.product_id.id,
								'issued_quant':quant.qty,
								'batch':quant.lot_id.id,
								'ref_id':dc_id.id,
							}

							ctx = {}
							ctx.update({'company_id':self.company_id})
							dc_line = dc_line_obj.with_context(ctx).new(dc_line_val)
							dc_line.onchange_product_id()
							val = dc_line._convert_to_write({line:dc_line[line] for line in dc_line._cache})
							dc_line_id = dc_line_obj.create(val)

			return dc_id

class StockMove(models.Model):

	_inherit = "stock.move"

	issue_line_id = fields.Many2one("warehouse.stock.issue.line", string="Issue line")

	def action_done(self, cr, uid, ids, context=None):
		res = super(StockMove, self).action_done(cr, uid, ids, context=context)
		for move in self.browse(cr, uid, ids, context=context):
			if move.issue_line_id:
				quant = move.product_uom_qty
				move.issue_line_id.issued_quant += quant
				move.issue_line_id.state = 'issue'
				move.issue_line_id.transfer_id.state = 'issue'
