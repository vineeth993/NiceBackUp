
from openerp import fields, models, api
from openerp.exceptions import ValidationError
from datetime import date
import datetime

import logging

_logger = logging.getLogger(__name__)

class MultiStockTransfer(models.Model):

	_name = "multi.stock.transfer"
	_order = "id desc"
	_inherit = ["mail.thread"]
	_description = "Multi Stock Transfer Request"

	def get_expected_date(self):
		today = date.today()
		expected_date = today + datetime.timedelta(days=4)
		return expected_date.strftime('%Y-%m-%d')

	def _get_picking_type(self):
		types = self.env["stock.picking.type"].search([("code", "=", "incoming"), ('warehouse_id.type', '=', 'finished'), ('warehouse_id.company_id', '=', self.env.user.company_id.id)])
		if not types:
			raise ValidationError("Make sure you have at least an incoming picking type defined")
		return types[0]

	def _amount_line_tax(self, line):
		val = 0.0
		price = line.unit_price
		qty = line.product_qty
		for c in line.taxes_id.compute_all(price, qty, line.product_id, line.transfer_id.partner_id)['taxes']:
			val += c.get('amount', 0.0)
		return val

	@api.depends('stock_line_id.issued_qty')
	def _get_is_issued(self):

		for line in self:
			val = any([item.issued_qty for item in line.stock_line_id])
			if val:
				line.update({
					'is_issued':True,
					})
			else:
				line.update({
					'is_issued':False
					})				

	@api.depends("stock_line_id.subtotal")
	def _compute_amount(self):
		
		res = {}
		for stock in self:
			res[stock.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
			}
			val = val1 =  0.0
			for line in stock.stock_line_id:
				val1 += line.subtotal
				val += self._amount_line_tax(line)

			stock.update({
                'amount_untaxed': val1,
                'amount_tax': val,
                'amount_total':val + val1,
                })


	name = fields.Char("Doc No", copy=False)	
	request_company_id = fields.Many2one("res.company", string="Requested To", required=True, track_visibility='always')
	partner_id = fields.Many2one("res.partner", string="Request To Partner", required=True, store=True)
	company_id = fields.Many2one("res.company", string="company", default=lambda self: self.env.user.company_id)
	stock_line_id = fields.One2many("multi.stock.transfer.line", "transfer_id", string="Reference", copy=True)
	state = fields.Selection([('draft', 'Draft'),
								('confirm', 'Confirm'),
								('process', 'Processing'),
								('issued', 'Issued'),
								('error', 'Error Rcvd'),
								('cancel', 'Cancel'),
								('done', 'Done')], string="Status", default="draft", track_visibility='onchange')
	request_date = fields.Datetime("Requested Date", required=True, select=True, readonly=True, default=lambda x: date.today(), states={"draft":[('readonly', False)]})
	expected_date = fields.Datetime("Expected Date", required=True, default=get_expected_date)
	picking_id = fields.Many2one("stock.picking.type", string="Picking",default=_get_picking_type, required=True)
	amount_untaxed = fields.Float("Taxable Value", compute="_compute_amount", store=True, track_visibility='always', copy=True)
	amount_tax = fields.Float("Taxes", compute="_compute_amount", store=True, track_visibility='always', copy=True)
	amount_total = fields.Float("Total", compute="_compute_amount", store=True, track_visibility='always', copy=True)
	currency_id = fields.Many2one("res.currency", invisible=True)
	reference = fields.Char("Reference", copy=False)
	quant_issued_date = fields.Datetime("Issued Date")
	is_issued = fields.Boolean(string="Issue", compute="_get_is_issued")
	issued_user = fields.Char("Issued User" , copy=False, readonly=True)

	@api.model
	def create(self, val):
		if val.get("name", "/") == '/':
			val["name"] = self.env["ir.sequence"].next_by_code("multi.stock.transfer")
		return super(MultiStockTransfer, self).create(val)

	@api.model
	def unlink(self):
		for line in self:
			if line.state != "draft":
				raise ValidationError("Document not able to delete")
		return super(MultiStockTransfer, self).unlink()

	@api.onchange("request_company_id")
	def onchange_request_company_id(self):
		for line in self:
			if line.request_company_id:
				line.partner_id = line.request_company_id.partner_id.id
				line.currency_id = line.request_company_id.partner_id.property_product_pricelist.currency_id.id

	@api.multi
	def action_cancel(self):

		picks = self.env['stock.picking'].search([('outward_id', '=', self.id), ('state', '!=', 'done')])
		if picks:
			for pick in picks:
				pick.action_cancel()
				
		if self.state in ('draft', 'confirm'):
			outward_id = self.env['multi.stock.outward'].sudo().search([('name', '=', self.reference)])
			outward_id.action_cancel()
			self.write({'state':'cancel'})
			for line in self.stock_line_id:
				line.action_cancel()

	@api.multi
	def action_confirm(self):
		inward_request = self.env["multi.stock.outward"]
		inward_request_line = self.env["multi.stock.outward.line"]
		types = self.env["stock.picking.type"].sudo().search([("code", "=", "outgoing"), ('warehouse_id.type', '=', 'finished'),('warehouse_id.company_id', '=', self.request_company_id.id)])

		if not self.stock_line_id:
			raise ValidationError("Please Specify the product")

		for value in self.stock_line_id:
			if value.product_qty <= 0:
				raise ValidationError("Product quantity cannot be zero")

		val = {'request_company_id':self.company_id.id,
				'company_id':self.request_company_id.id,
				'reference':self.name,
				'expected_date':self.expected_date,
				'picking_id': types[0].id,
				'created_user':self.env.user.name
				}
		inward = inward_request.sudo().new(val)
		inward.onchange_request_company_id()
		val = inward._convert_to_write({line:inward[line] for line in inward._cache})
		outward_id = inward_request.sudo().create(val)

		for value in self.stock_line_id:
			val= {'product_id':value.product_id.id,
				   'product_qty':value.product_qty,
				   'transfer_id':outward_id.id,
				   'reference_line':value.id,
				   'batch':value.batch.id
				}


			ctx = {}
			ctx.update({'default_picking':types[0].id, 'company_id':self.request_company_id.id, 'default_date':self.expected_date})
			inward_line = inward_request_line.sudo().with_context(ctx).new(val)
			inward_line.onchange_product_id()
			inward_line.update({'unit_price':value.unit_price})
			val = inward_line._convert_to_write({line:inward_line[line] for line in inward_line._cache})
			inward_request_line_id = inward_request_line.sudo().create(val)
			
			value.update({'state':'confirm'})
			value.sudo().write({'outward_line_id' : inward_request_line_id.id, 'quantity_remain':value.product_qty})
		self.write({'state':'confirm', 'reference':outward_id.name})
				
	@api.multi
	def action_progress(self):
		stock_picking_obj = self.env['stock.picking']
		stock_move_obj = self.env['stock.move']
		if not self.stock_line_id:
			raise ValidationError("Please Specify the product")
		val = {'partner_id':self.partner_id.id,
				'move_type':'direct',
				'invoice_state':'none',
				'picking_type_id':self.picking_id.id,
				'origin':self.name,
				'inward_id':self.id
				}

		stock_id = stock_picking_obj.create(val)
		self.write({'state':'process'})
			
		for value in self.stock_line_id:
			val = {
				'name':value.product_id.name,
				'product_id':value.product_id.id,
				'product_uom': value.product_uom.id,
				'product_uom_qty':value.product_qty,
				'picking_id':stock_id.id,
				'location_id':value.source_location.id,
				'location_dest_id':value.destination_location.id,
				}
			value.update({'state':'process'})
			stock_move_obj.create(val)
		stock_id.action_confirm()

	@api.multi
	def action_done(self):
		packing_obj = self.env['stock.pack.operation']
		outward_ref_id = self.env["multi.stock.outward"].sudo().search([('name', '=', self.reference)])
		stock_picking_id = self.env['stock.picking'].search([('inward_id', '=', self.id),('state','not in', ('draft', 'cancel', 'done'))])
		pack_ids = []
		update_qty = 0
		qty_remain = []
		qty_stat = []
		for line in self.stock_line_id:
			if line.issued_qty or line.recieved_qty:
				if line.issued_qty:
					val = {
						'picking_id':stock_picking_id.id,
						'product_uom_id':line.product_uom.id,
						'product_id':line.product_id.id,
						'product_qty':line.issued_qty,
						'location_dest_id':line.destination_location.id,
						'location_id':line.source_location.id,
						'lot_id':line.batch.id
					}
					pack_id = packing_obj.create(val)
					pack_ids.append(pack_id)
				qty = line.recieved_qty - line.issued_qty
				line.quantity_remain = line.quantity_remain - line.issued_qty
				line.issued_qty = 0
				line.recieved_qty = 0
				qty_list = []

				if qty:
					update_qty = line.outward_line_id.qty_anomaly + qty
					qty_list.append(update_qty)
				else:
					update_qty = 0
					qty_list.append(0)

				if update_qty > 0:
					line.write({'state':'excess', 'error_issued':update_qty})
					line.outward_line_id.sudo().write({'state':'excess', 'qty_anomaly':update_qty})
				elif update_qty < 0:
					line.write({'state':'less', 'error_issued':update_qty})
					line.outward_line_id.sudo().write({'state':'less', 'qty_anomaly':update_qty})
				elif line.error_issued:
					state = 'less' if line.error_issued < 0 else 'excess'
					line.write({'state':state, 'error_issued':line.error_issued})
					line.outward_line_id.sudo().write({'state':state, 'qty_anomaly':line.error_issued})
				elif line.quantity_remain:
					line.write({'state':'process', 'error_issued':0})
					line.outward_line_id.sudo().write({'state':'process', 'qty_anomaly':0})
				else:
					line.write({'state':'done', 'error_issued':0})
					line.outward_line_id.sudo().write({'state':'done', 'qty_anomaly':0})
			qty_remain.append(line.quantity_remain)
			qty_stat.append(line.state)

		if pack_ids:
			stock_picking_id.write({'pack_operation_ids':[(6, 0, pack_ids)]})
			stock_picking_id.do_transfer()

		if any(qty_list) or 'exces' in qty_stat or 'less' in qty_stat:
			state = 'error'
		elif not any(qty_remain):
			state = 'done'
		else:
			state = 'process'
		outward_ref_id.sudo().write({'state':state})
		self.write({'state':state})

	def action_view(self, cr, uid, ids, context=None):

		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		pick_obj = self.pool.get('stock.picking')

		result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree_all')
		id = result and result[1] or False
		result = act_obj.read(cr, uid, [id], context=context)[0]

		pick_ids = []
		pick_ids = pick_obj.search(cr, uid, [('inward_id', '=', ids)], context=context)
		
		if len(pick_ids) > 1:
			result['domain'] = "[('id','in',["+','.join(map(str, pick_ids))+"])]"
		else:
			res = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_form')
			result['views'] = [(res and res[1] or False, 'form')]
			result['res_id'] = pick_ids and pick_ids[0] or False

		return result


class MultiStockLine(models.Model):

	_name = "multi.stock.transfer.line"

	def _get_recieved_qty(self):
		if self.issued_qty:
			return self.issued_qty
		return 0

	@api.depends("product_qty", "unit_price")
	def _get_amount(self):
		for line in self:
			line.subtotal = line.product_qty * line.unit_price


	product_id = fields.Many2one("product.product", string="Product", required=True, copy=True)
	product_qty = fields.Float("Req.Qty", required=True, copy=True)
	quantity_remain = fields.Float("Pending Qty", readonly=True)
	issued_qty = fields.Float("Issue Qty",copy=False)
	recieved_qty = fields.Float("Recvd.Qty", default=_get_recieved_qty, copy=False)
	transfer_id = fields.Many2one("multi.stock.transfer", string="Reference")
	taxes_id = fields.Many2many("account.tax", "taxes_in_product_line_stock_transfer", "partner_id", "taxes_id", "Taxes", copy=True)
	unit_price = fields.Float("Unit Price", copy=True)
	subtotal = fields.Float("Subtotal", compute="_get_amount", store=True, copy=True)
	state = fields.Selection([('draft', 'Draft'),
								('confirm', 'Confirm'),
								('process', 'Processing'),
								('issued', 'Issued'),
								('less', 'Short Issued'),
								('excess', 'Excess Issued'),
								('cancel', 'Cancel'),
								('done', 'Done')], string="Status", default="draft", store=True, readonly=True)
	product_uom = fields.Many2one("product.uom", string="Unit", copy=True)
	source_location = fields.Many2one("stock.location", string="Source Location", copy=True)
	destination_location = fields.Many2one("stock.location", string="Destination Location", copy=True)
	partner_id = fields.Many2one('res.partner', related="transfer_id.partner_id")
	outward_line_id = fields.Many2one('multi.stock.outward.line', string="Outward Ref")
	error_issued = fields.Float("Error Qty", copy=False)
	date_time = fields.Datetime("Req Date")
	batch = fields.Many2one("stock.production.lot", string="Batch")

	@api.onchange("product_id")
	def onchange_product_id(self):
		for line in self:
			taxes_id = []
			if not line.product_id:
				return None
			line.product_uom = line.product_id.uom_id.id
			if line._context.get('default_picking', '/') != '/':
				picking_id = line.env['stock.picking.type'].browse(line._context.get('default_picking'))
				line.source_location = picking_id.default_location_src_id
				line.destination_location  = picking_id.default_location_dest_id
			if line._context.get("company_id", '/') != '/':
				taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id.id == line._context.get("company_id"))
			else:
				taxes = line.product_id.taxes_id
			if line._context.get('default_date', '/') != '/':
				line.date_time = line._context.get('default_date')
			for tax in taxes:
				if tax.tax_categ == 'gst':
					taxes_id.append(tax.id)
			
			line.taxes_id = taxes_id
			line.unit_price = (line.product_id.lst_price *25)/100

	@api.multi
	def action_cancel(self):
		self.write({'state':'cancel'})