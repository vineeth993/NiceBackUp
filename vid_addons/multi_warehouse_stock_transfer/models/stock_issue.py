from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime as date
import datetime
import base64

import logging

_logger = logging.getLogger(__name__)

class StockWarehouseIssue(models.Model):

	_name = "warehouse.stock.issue"
	_inherit = ["mail.thread", "ir.needaction_mixin"]
	_description = "Stock Tranfer Outwards"
	_order = "id desc"

	def get_expected_date(self):
		today = date.now()
		expected_date = today + datetime.timedelta(days=20)
		return expected_date.strftime('%Y-%m-%d')

	def _get_picking_type(self):
		types = self.env["stock.picking.type"].search([("code", "=", "outgoing"), ('warehouse_id.type', '=', 'finished'),('warehouse_id.company_id', '=', self.env.user.company_id.id)])
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

	@api.depends("dc_ids")
	def _get_dc(self):
		for issue in self:
			if issue.dc_ids:
				issue.update({
					"dc_exists":True
					})

	name = fields.Char("Doc No", copy=False)
	request_warehouse_from_id = fields.Many2one("stock.warehouse", string="Requested From", required=True, track_visibility='onchange')
	partner_id = fields.Many2one("res.partner", string="Request From Partner", required=True, store=True)
	warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True)
	company_id = fields.Many2one("res.company", string="company", default=lambda self: self.env.user.company_id)
	stock_line_id = fields.One2many("warehouse.stock.issue.line", "transfer_id", string="Reference")
	state = fields.Selection([('draft', 'Draft'),
								('confirm', 'Accepted'),
								('issue', 'Issued'),
								('process','Processing'),
								('error', 'Qty Mismatch'),
								('cancel', 'Cancel'),
								('done', 'Done')], string="Status", default="draft", track_visibility='onchange')
	request_date = fields.Datetime("Requested Date", required=True, select=True, readonly=True, default=lambda x: date.now(), states={"draft":[('readonly', False)]})
	expected_date = fields.Datetime("Expected Date", required=True, default=get_expected_date)
	picking_id = fields.Many2one("stock.picking.type", string="Picking",default=_get_picking_type, required=True)
	amount_untaxed = fields.Float("Taxable Value", compute="_compute_amount", store=True, track_visibility='always')
	amount_tax = fields.Float("Taxes", compute="_compute_amount", store=True, track_visibility='always')
	amount_total = fields.Float("Total", compute="_compute_amount", store=True, track_visibility='always')
	currency_id = fields.Many2one("res.currency", invisible=True)
	reference = fields.Many2one("warehouse.stock.request", string="Reference", readonly=True)
	dc_ids = fields.Many2many("dc.warehouse", "issue_dc_relation", "issue_id", "dc_id", string="DC's")
	dc_exists = fields.Boolean("DC", compute="_get_dc", default=False)

	@api.model
	def _needaction_domain_get(self):
		return [('state', '=', 'draft')]

	@api.multi
	def create(self, val):
		if val.get('name', '/') == '/':
			warehouse_id = self.env['stock.warehouse'].browse(val.get('warehouse_id'))
			if warehouse_id.issue_seq:
				seq_obj = self.env['ir.sequence']
				val['name'] = seq_obj.next_by_id(warehouse_id.issue_seq.id)
			else:
				raise ValidationError("Please create an issue sequence for %s"%(warehouse_id.name))
		return super(StockWarehouseIssue, self).create(val)


	@api.onchange("request_warehouse_from_id")
	def onchange_request_company_id(self):
		for line in self:
			if line.request_warehouse_from_id:
				line.partner_id = line.request_warehouse_from_id.partner_id.id
				line.currency_id = line.company_id.partner_id.property_product_pricelist.currency_id.id

	@api.multi
	def action_confirm(self):
		stock_picking_obj = self.env['stock.picking']
		stock_move_obj = self.env['stock.move']

		if not self.stock_line_id:
			raise ValidationError("Please Specify the product")

		if self.reference.state == 'cancel':
			raise ValidationError("The reference document is canceled")

		val = {'partner_id':self.partner_id.id,
				'move_type':'direct',
				'invoice_state':'none',
				'picking_type_id':self.picking_id.id,
				'origin':self.name,
				'issue_id':self.id,
				'is_dc':True
				}

		stock_id = stock_picking_obj.create(val)
		self.write({'state':'confirm'})

		self.reference.action_progress()

		for value in self.stock_line_id:
			value.qty_remain = value.product_qty
			val = {
				'name':value.product_id.name,
				'product_id':value.product_id.id,
				'product_uom': value.product_uom.id,
				'product_uom_qty':value.product_qty,
				'picking_id':stock_id.id,
				'location_id':value.source_location.id,
				'location_dest_id':value.destination_location.id,
				'issue_line_id':value.id,
				}
			value.write({'state':'confirm'})
			stock_move_obj.create(val)
		stock_id.action_confirm()

	@api.multi
	def action_move(self):
	
		self.reference.write({'state':'issued', 'quant_issued_date':date.now()})
		for item in self.stock_line_id:
			item.last_issued_stock = 0
			if item.issued_quant:
				quant = item.issued_quant
				pending = item.qty_remain - item.issued_quant
				issued_quant = item.reference_line.issued_qty + item.issued_quant
				item.reference_line.write({'issued_qty':issued_quant, 'recieved_qty':issued_quant, 'state':'issued'})
				item.update({"issued_quant": 0.0, "qty_remain":pending, 'state':'moved'})
			elif item.qty_remain:
				item.update({'state':'process'})

	@api.multi
	def action_cancel(self):
		picks = self.env['stock.picking'].search([('issue_id', '=', self.id), ('state', '!=', 'done')])
		if picks:
			for pick in picks:
				pick.action_cancel()
		self.write({'state':'cancel'})
		for line in self.stock_line_id:
			line.action_cancel()

	@api.multi
	def action_view_dc(self):
		if self.dc_ids:
			ids = [dc.id for dc in self.dc_ids]

		if ids:
			domain = [('id', 'in', ids)]
			action =  {
				'name':_('Warehouse DC'),
				'view_type':'form',
				'view_mode':'tree,form',
				'res_model':'dc.warehouse',
				'type':'ir.actions.act_window',
				'domain':domain,
				'target':'current',
			}
			return action

	@api.multi
	def action_done(self):
		dc_ids = [dc.id for dc in self.dc_ids]

		get_dcs = self.env['warehouse.dc'].search([('id', 'in', dc_ids), ('state', '=', 'dc')])
		if get_dcs:
			get_dcs.action_done()


	def action_view(self, cr, uid, ids, context=None):

		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		pick_obj = self.pool.get('stock.picking')

		result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree_all')
		id = result and result[1] or False
		result = act_obj.read(cr, uid, [id], context=context)[0]

		pick_ids = []
		pick_ids = pick_obj.search(cr, uid, [('issue_id', 'in', ids)], context=context)
		
		if len(pick_ids) > 1:
			result['domain'] = "[('id','in',["+','.join(map(str, pick_ids))+"])]"
		else:
			res = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_form')
			result['views'] = [(res and res[1] or False, 'form')]
			result['res_id'] = pick_ids and pick_ids[0] or False

		return result


class StockWarehouseIssueLine(models.Model):

	_name = "warehouse.stock.issue.line"

	@api.depends("product_qty", "unit_price")
	def _get_amount(self):
		for line in self:
			line.subtotal = line.product_qty * line.unit_price

	product_id = fields.Many2one("product.product", string="Product", required=True)
	product_qty = fields.Float("Req.Qty", required=True)
	transfer_id = fields.Many2one("warehouse.stock.issue", string="Reference")
	taxes_id = fields.Many2many("account.tax", "taxes_in_product_line_stock_outward_transfer", "partner_id", "taxes_id", "Taxes")
	unit_price = fields.Float("Unit Price")
	subtotal = fields.Float("Subtotal", compute="_get_amount", store=True)
	state = fields.Selection([('draft', 'Draft'),
								('confirm', 'Confirm'),
								('less', 'Short Issued'),
								('excess', 'Excess Issued'),
								('issue', 'Issued'),
								('moved', 'DC Issued'),
								('process', 'Processing'),
								('cancel', 'Cancel'),
								('done', 'Done')], string="Status", default="draft", store=True)
	product_uom = fields.Many2one("product.uom", string="Unit")
	source_location = fields.Many2one("stock.location", string="Source Location")
	destination_location = fields.Many2one("stock.location", string="Destination Location")
	partner_id = fields.Many2one('res.partner', related="transfer_id.partner_id")
	issued_quant = fields.Float(string='Issue Qty')
	qty_remain = fields.Float(string='Pending Qty')
	qty_anomaly = fields.Float(string='Error Qty')
	reference_line = fields.Many2one("warehouse.stock.request.line", string="Reference")
	date_time = fields.Datetime("Exp Date")

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
				_logger.info("The company_id = "+str(line._context.get("company_id", '/')))
				# company = line._context.get("company_id", '/')
				taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id == line._context.get("company_id"))
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
