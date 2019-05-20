
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

from datetime import datetime as date
import datetime
import base64

import logging 

_logger = logging.getLogger(__name__)


class WarehouseDc(models.Model):

	_name = "dc.warehouse"
	_inherit = ["mail.thread", "ir.needaction_mixin"]
	_description = "Warehouse DC"
	_order = "id desc"

	def _amount_line_tax(self, line):

		val = 0.0
		price = line.unit_price
		qty = line.issued_quant
		for c in line.taxes_id.compute_all(price, qty, line.product_id, line.ref_id.partner_id)['taxes']:
			val += c.get('amount', 0.0)
		return val


	@api.depends("line_id.subtotal")
	def _compute_amount(self):

		res = {}
		for stock in self:
			res[stock.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
			}
			val = val1 =  0.0
			for line in stock.line_id:
				val1 += line.subtotal
				val += self._amount_line_tax(line)

			stock.update({
				'amount_untaxed': val1,
				'amount_tax': val,
				'amount_total':val + val1,
				})


	name = fields.Char("no", copy=False)
	dc_number = fields.Char("DC No")
	request_warehouse_from_id = fields.Many2one("stock.warehouse", string="Requested From", required=True, track_visibility='onchange')
	partner_id = fields.Many2one("res.partner", string="Request From Partner", required=True, store=True)
	warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True)
	company_id = fields.Many2one("res.company", string="company", default=lambda self: self.env.user.company_id)
	state = fields.Selection([('draft', 'Draft'),
								('dc', 'Can Move'),
								('done', 'Done'),
								('cancel', 'Cancel')], string="Status", default="draft", track_visibility='onchange', copy=False)
	request_date = fields.Datetime("Requested Date", required=True, select=True, readonly=True, default=lambda x: date.now(), states={"draft":[('readonly', False)]})
	amount_untaxed = fields.Float("Taxable Value", compute="_compute_amount", store=True, track_visibility='always')
	amount_tax = fields.Float("Taxes", compute="_compute_amount", store=True, track_visibility='always')
	amount_total = fields.Float("Total", compute="_compute_amount", store=True, track_visibility='always')
	currency_id = fields.Many2one("res.currency", invisible=True)
	reference = fields.Many2one("warehouse.stock.request", string="Reference", readonly=True)
	issue_refernce = fields.Many2one("warehouse.stock.issue", string="Issue Reference", readonly=True)
	quant_issued_date = fields.Date("Issued Date")
	json_file = fields.Binary("E-Way Bill-Json")
	json_file_name = fields.Char("File name")
	line_id = fields.One2many("dc.warehouse.line", "ref_id", string="Reference", copy=True)

	@api.multi
	def action_validate(self):
		if self.warehouse_id.dc_seq:
			seq_obj = self.env['ir.sequence']
			self.name = seq_obj.next_by_id(self.warehouse_id.dc_seq.id)
			self.dc_number = self.name
		else:
			raise ValidationError("Please create an dc sequence for %s"%(warehouse_id.name))
		
		for line in self.line_id:
			line.write({'state':'done'})

		date_today = date.now()
		self.create_request_grn()
		self.issue_refernce.write({'dc_ids':[(4, self.id)]})
		self.issue_refernce.action_move()
		self.write({'quant_issued_date':date_today, 'state':'dc'})

	def create_request_grn(self):
		
		packing_obj = self.env['stock.pack.operation']
		stock_picking_id = self.env['stock.picking'].search([('request_id', '=', self.reference.id),('state','not in', ('draft', 'cancel', 'done'))])
		location_id = self.reference.picking_id.default_location_src_id
		location_dest_id = self.reference.picking_id.default_location_dest_id
		pack_ids = []
		existing_package_ids = packing_obj.search([("picking_id", "=", stock_picking_id.id)])
		
		if existing_package_ids:
			existing_package_ids.unlink()

		for line in self.line_id:
			val = {
					'picking_id':stock_picking_id.id,
					'product_uom_id':line.product_uom.id,
					'product_id':line.product_id.id,
					'product_qty':line.issued_quant,
					'location_dest_id':location_dest_id.id,
					'location_id':location_id.id,
					'lot_id':line.batch.id
				}

			pack_id = packing_obj.create(val)
			# pack_ids.append(pack_id.id)
		# if pack_ids:
			stock_picking_id.write({'pack_operation_ids':[(4, pack_id.id)]})
			# stock_picking_id.do_transfer()

	@api.model
	def _needaction_domain_get(self):
		return [('state', '=', 'draft')]

	@api.multi
	def action_print_dc(self):
		return self.env['report'].get_action(self, 'multi_warehouse_stock_transfer.report_dc')

	@api.multi
	def action_cancel(self):
		self.write({'name':"", 'state':'cancel'})
		for line in self.line_id:
			line.write({'state':'cancel'})


class WarehouseDcLine(models.Model):

	_name = "dc.warehouse.line"

	@api.depends("issued_quant", "unit_price")
	def _get_amount(self):
		for line in self:
			line.subtotal = line.issued_quant * line.unit_price

	product_id = fields.Many2one("product.product", string="Product", required=True)
	taxes_id = fields.Many2many("account.tax", "taxes_in_product_line_warehouse_dc", "partner_id", "taxes_id", "Taxes")
	unit_price = fields.Float("Unit Price")
	subtotal = fields.Float("Subtotal", compute="_get_amount", store=True)
	state = fields.Selection([('draft', 'Draft'),
								('done', 'Done'),
								('cancel', 'Cancel')], string="Status", default="draft", store=True)
	product_uom = fields.Many2one("product.uom", string="Unit")
	partner_id = fields.Many2one('res.partner', related="ref_id.partner_id")
	issued_quant = fields.Float(string='Issue Qty')
	batch = fields.Many2one("stock.production.lot", string="Batch")
	ref_id = fields.Many2one("dc.warehouse", string="Reference")

	@api.onchange("product_id")
	def onchange_product_id(self):
		for line in self:
			taxes_id = []
			if not line.product_id:
				return None
			line.product_uom = line.product_id.uom_id.id
			if line._context.get("company_id", '/') != '/':
				# company = line._context.get("company_id", '/')
				taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id == line._context.get("company_id"))
			else:
				taxes = line.product_id.taxes_id
			for tax in taxes:
				if tax.tax_categ == 'gst':
					taxes_id.append(tax.id)
			
			line.taxes_id = taxes_id
			line.unit_price = (line.product_id.lst_price *25)/100
