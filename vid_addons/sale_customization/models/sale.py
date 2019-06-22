# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
from docutils.nodes import Part
import logging
from openerp.exceptions import ValidationError, except_orm

_logger = logging.getLogger(__name__)

class SaleReasonCategory(models.Model):
	_name = 'sale.reason.category'

	name = fields.Char("Category")


class SaleReason(models.Model):
	_name = 'sale.reason'

	name = fields.Char(string='Reason For Sale', required=True)
	desc = fields.Text(string='Description')
	group_categ = fields.Many2one('sale.reason.category', string='Group Category')
	profiling_seasons1 = fields.Many2many('product.template', 'product_template_sale_reason_rel',
										  'sale_reason_id', 'product_template_id',
										  string='Profiling Season', invisible=True)

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	_order = 'order_id desc, sequence, id'
   
	@api.depends('product_id', 'order_id.partner_id', 'order_id.partner_selling_type', 'order_id.normal_disc', 'order_id.nonread_normal_disocunt', 'order_id.nonread_extra_disocunt', 'order_id.extra_discount')
	def _get_product_values(self):
		tax_ids = []
		taxes_ids = []
		for line in self:
			taxes_ids = []
			gst, igst, formstate, forminter = False, False, False, False
			sub_type_id = line.order_id.sub_type_id
			company = self.env['res.users'].browse(self._uid).company_id

			if sub_type_id:
				if sub_type_id and sub_type_id.tax_categ == 'gst':
					gst = True
					igst, formstate, forminter = False, False, False
				elif sub_type_id and sub_type_id.tax_categ == 'igst':
					gst, formstate, forminter = False, False, False
					igst = True
				elif sub_type_id and sub_type_id.tax_categ == 'formstate':
					gst, igst, forminter = False, False, False
					formstate = True
				elif sub_type_id and sub_type_id.tax_categ == 'forminter':
					gst, igst, formstate = False, False, False
					forminter = True
				else:
					gst, igst, formstate, forminter = False, False, False, False
			fpos = line.order_id.partner_id.property_account_position
			if gst or igst:
				for prod_tax in line.product_id.taxes_id:
					if prod_tax.company_id.id == company.id:
						if gst:
							if prod_tax.tax_categ == 'gst':
								taxes_ids.append(prod_tax.id)
						elif igst:
							if prod_tax.tax_categ == 'igst':
								taxes_ids.append(prod_tax.id)

			elif formstate or forminter:
				for partner_tax in line.order_partner_id.tax_id:
					if partner_tax.company_id.id == company.id:
						if formstate:
							if partner_tax.tax_categ == 'gst':
								taxes_ids.append(partner_tax.id)
						elif forminter:
							if partner_tax.tax_categ == 'igst':
								taxes_ids.append(partner_tax.id)
			line.tax_id = taxes_ids
			line.case_lot = line.product_id.case_lot
			taxes = line.product_id.taxes_id
			taxes_id = self.env['account.fiscal.position'].map_tax(taxes)
			tax=[]

			if line.partner_type != line.order_id.partner_selling_type:
				line.update({'partner_type':line.order_id.partner_selling_type})
				# line.partner_type = line.order_id.partner_selling_type
				# _logger.info("Partner Type = "+str(line.order_id.currency_id ))
				# line.price_unit = line.product_id.list_price
				if line.product_id.price_list and line.partner_type != 'special':
					raise exceptions.Warning('These Products cannot be quoted in Normal and Extra bill type = '+str(line.product_id.name))

			if line.order_id.partner_selling_type == 'normal' or line.order_id.partner_selling_type == 'extra':
				line.price_unit = line.product_id.list_price
			for pro_tax in taxes_id:
				tax.append(pro_tax.id)
			if line.partner_type != "special":
				line.discount = line.order_id.normal_disc
			else:
				line.discount = line.order_id.nonread_normal_disocunt
			if line.partner_type != 'normal':
				line.extra_discount = line.order_id.nonread_extra_disocunt
			else:
				line.extra_discount = line.order_id.extra_discount

	@api.depends("invoice_lines")
	def _get_invoiced_quant(self):
		for res in self:
			invoice_quant = 0
			for invoice in res.invoice_lines:
				invoice_quant += invoice.quantity
			res.invoiced_quant = invoice_quant
	
	reason = fields.Many2many('sale.reason', string="Purpose", related='product_id.profiling_seasons')
	product_uom_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product UoS'), default=0.0,
		required=True, readonly=True, states={'draft': [('readonly', False)]})
	discount = fields.Float('Discount (%)',compute='_get_product_values', digits_compute= dp.get_precision('Discount'), readonly=True, states={'draft': [('readonly', False)]}, store=True)
	tax_id = fields.Many2many('account.tax', 'sale_order_tax', 'order_line_id', 'tax_id', 'Taxes',compute='_get_product_values' ,readonly=True, states={'draft': [('readonly', False)]}, domain=['|', ('active', '=', False), ('active', '=', True)])
	extra_discount = fields.Float('Extra Discount (%)',compute='_get_product_values', digits_compute= dp.get_precision('Discount'), readonly=True)
	additional_discount = fields.Float('Scheme Discount (%)', digits_compute=dp.get_precision('Discount'))
	partner_type = fields.Char(string="Partner")
	sale_sub_type = fields.Char(string="Sub Type")
	product_name = fields.Char(string="Prod Name")
	order_partner_id = fields.Many2one("res.partner")
	case_lot = fields.Float('Case Lot', compute="_get_product_values", store=True)
	ordered_qty = fields.Float('Ordered Qty', readonly=True)
	product_location = fields.Many2one('stock.location', string="Warehouse")
	invoiced_quant = fields.Float("Invoiced Quant", compute="_get_invoiced_quant", store=True)

	def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
			uom=False, qty_uos=0, uos=False, name='', partner_id=False,
			lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
		res = super(SaleOrderLine, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
			name=name, partner_id=partner_id, lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
			fiscal_position=fiscal_position, flag=flag, context=context)
		
		partner_obj = self.pool.get('res.partner')
		partner_id = partner_obj.browse(cr, uid, partner_id)

		res["value"]["order_partner_id"] = partner_id.id

		# if context.get('sub_type_id', '/') != '/':
		#     res['value']['sale_sub_type'] = context.get('sub_type_id')

		# if context.get("partner_type", '/') != '/':
		#     res['value']['partner_type'] = context.get("partner_type")
		if res and 'price_unit' in res['value'] and res['value']['price_unit'] <=0 :
			raise exceptions.Warning('Product Price cannot zero or less than zero.')
		if product:
			product_obj = self.pool.get('product.product').browse(cr, uid, product)
			res['value']['product_name'] = product_obj.name
			res["value"]["product_location"] = product_obj.product_tmpl_id.product_location
			if product_obj.price_list and res['value']['partner_type'] != 'special':
				raise exceptions.Warning('These Products cannot be quoted in Normal and Extra bill type')

		return res

	@api.onchange('price_unit')
	def onchange_price_unit(self):
		for line in self: 
			if line.order_id.partner_selling_type != 'special':
				if line.product_id and line.price_unit != line.product_id.lst_price:
					line.update({
						'price_unit':line.product_id.lst_price
						})

class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'
	
	type = fields.Selection([
			('raw', 'Raw Materials'),
			('manufacture', 'Manufacturing'),
			('semi-finished', 'Semi Finished'),
			('finished', 'Finished'),
			])

class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	@api.depends('order_line.price_subtotal', 'extra_discount', 'normal_disc', 'nonread_extra_disocunt', 'nonread_normal_disocunt', 'partner_selling_type')
	def _amount_all(self):
		"""
		Compute the total amounts of the SO.
		"""
		
		cur_obj = self.pool.get('res.currency')
		res = {}
		for order in self:
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
			}
			val = val1 = add_disc =  0.0
			cur = order.pricelist_id.currency_id
			for line in order.order_line:
				val1 += line.price_subtotal
				val += self._amount_line_tax(line)
			order.update({
				'amount_untaxed': cur.round(val1),
				'amount_tax': cur.round(val),
				'amount_total':cur.round(val) + cur.round(val1),
				})
			
	def _get_warehouse(self):
		warehouse_ids = self.env['stock.warehouse'].search([('type', '=', 'finished')])
		if not warehouse_ids:
			return False
		return warehouse_ids[0]
	
	@api.depends('brand_id', 'partner_selling_type', 'partner_id')
	def _get_extra_discount(self):
		for order in self:
			if order.brand_id:
				if not order.partner_id:
					order.brand_id = None
					raise ValidationError("Please select partner before selecting product brand")
				if order.partner_selling_type in ('normal', 'extra'):
					partner_brand_id = order.env['partner.discount'].search([('partner_id', '=', order.partner_id.id), ('category_id', '=', order.brand_id.id)])
					if partner_brand_id and order.partner_selling_type == 'normal':
						order.normal_disc = partner_brand_id.normal_disc
						order.extra_discount = partner_brand_id.additional_disc
					elif partner_brand_id and order.partner_selling_type == 'extra':
						order.normal_disc = partner_brand_id.normal_disc
						order.extra_discount = 0.00
					else:
						order.normal_disc = 0.00
						order.extra_discount = 0.00
				else:
					order.normal_disc = 0.00
					order.extra_discount = 0.00

	
				# if item:
			#     raise exceptions.Warning('This product does not belong to this brand = '+str(item))

	transaction_type = fields.Selection([('normal', 'Normal'), ('sample', 'Sample')], 'Bill Type', default="normal")
	normal_disc = fields.Float("Normal Discount", compute="_get_extra_discount", store=True)
	partner_selling_type = fields.Selection([('normal', 'Normal'), ('special', 'Special'), ('extra', 'Extra')], string='Price Type', default="normal")
	extra_discount = fields.Float('Additional Discount(%)', compute='_get_extra_discount',digits_compute=dp.get_precision('Account'), store=True)
	nonread_extra_disocunt = fields.Float('Additional Discount(%)', digits_compute=dp.get_precision('Account'), copy=False)
	nonread_normal_disocunt = fields.Float('Normal Discount', digits_compute=dp.get_precision('Account'), copy=False)
	state = fields.Selection([
			('draft', 'Draft Quotation'),
			('confirm', 'Quotation Confirmed'),
			('sent', 'Quotation Sent'),
			('cancel', 'Cancelled'),
			('waiting_date', 'Waiting Schedule'),
			('progress', 'Sales Order'),
			('manual', 'Sale to Invoice'),
			('shipping_except', 'Shipping Exception'),
			('invoice_except', 'Invoice Exception'),
			('done', 'Done'),
			], 'Status', readonly=True, copy=False, select=True)
	order_line = fields.One2many('sale.order.line', 'order_id', 'Order Lines',
		readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True)
	warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True, default=_get_warehouse)
	amount_untaxed = fields.Float(string='Taxable Value', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	amount_tax = fields.Float(string='Taxes', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	employee_id = fields.Many2one("hr.employee", string="Quotation Signer")
	delivery_term = fields.Many2one("sale.delivery.term", string="Delivery Terms")
	validity_term = fields.Many2one("sale.validity.term", string="Validity Terms")
	other_terms = fields.Many2one("sale.delivery.term", string="Other Terms")
	tax_stat = fields.Boolean("Inclusive of Tax")
	on_letter_head = fields.Boolean("Quotation Letter Head")
	discount_stat = fields.Boolean("Discount")
	brand_id = fields.Many2one("product.brand", string="Product Type")
	validated_user = fields.Many2one('res.users', string="Validated User")

	def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
		loc_obj = self.pool.get("stock.location")
		res = super(SaleOrder, self)._prepare_order_line_procurement(cr, uid, order, line, group_id=group_id, context=context)
		res['name'] = line.product_name
		#warehouse_id = loc_obj.get_warehouse(cr, uid, line.product_location, context=context)
		#res['warehouse_id'] = warehouse_id or order.warehouse_id.id or False
		return res

	@api.multi
	def action_ship_recreate(self):
		self.signal_workflow('ship_recreate')

	@api.multi
	def onchange_partner_id(self, partner_id):
		res = super(SaleOrder, self).onchange_partner_id(partner_id)
		if partner_id:
			partner = self.env['res.partner'].browse(partner_id)
			if not partner.email or not partner.mobile or not partner.street:
				raise ValidationError("Please Update Customer Master With Following Data\n1. Email\n2. Mobile\n3. Address ")
		return res



	@api.multi
	def action_quotation_confirm(self):
		self.state = 'confirm'
		order_lines = self.env['sale.order.line'].search([('order_id', '=', self.id)], order='product_name')
		seq = 1
		self.validated_user = self.env.user
		for line in order_lines:
			line.sequence = seq
			seq += 1
			if line.product_uom_qty <= 0:
				raise exceptions.Warning('Quantity cannot be less than zero')
	
	@api.multi
	def action_button_confirm(self):
		order_line_obj = self.env['sale.order.line']
		order_lines = self.env['sale.order.line'].search([('order_id', '=', self.id)], order='product_name')
		seq = 1
		temp_product = {}
		for line in order_lines:
			line.sequence = seq
			seq += 1
			if line.product_uom_qty <= 0:
				raise exceptions.Warning('Quantity cannot be less than zero')                
		return super(SaleOrder, self).action_button_confirm()
	
	def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_invoice = False, context=None):
		inv_obj = self.pool.get("account.invoice")
		res = super(SaleOrder,self).action_invoice_create(cr, uid, ids, grouped=grouped, states=states, date_invoice = date_invoice, context=context)
		for order in self.browse(cr, uid, ids, context=context):
			vals = {'partner_selling_type':order.partner_selling_type,
					'normal_disc':order.normal_disc,
					'extra_discount':order.extra_discount,
					'nonread_extra_disocunt':order.nonread_extra_disocunt,
					'nonread_normal_disocunt':order.nonread_normal_disocunt
					}
			inv_obj.write(cr, uid, res, vals, context=context)
		return res

class SaleDeliveryTerm(models.Model):

	_name = "sale.delivery.term"
	_description = "Stock Delivery Terms"

	name = fields.Char('Delivery Terms', required=True)
	note = fields.Text('Description')
	others = fields.Boolean('Other Terms', help="Please check if it is other terms")
	active = fields.Boolean('Active', help="If the active field is set to False, it will allow you to hide the Delivery term without removing it.", default=True)

class SaleValidityTerm(models.Model):

	_name = "sale.validity.term"
	_description = "Quotation Validity Terms"

	name = fields.Char('Validity Terms', required=True)
	note = fields.Text('Description')
	active = fields.Boolean('Active', help="If the active field is set to False, it will allow you to hide the Validity term without removing it.", default=True)

