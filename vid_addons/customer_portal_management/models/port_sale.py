
from openerp import models, api, fields, _
from openerp.exceptions import ValidationError
from datetime import date
import logging
from datetime import datetime
import xlrd
import tempfile
import base64

_logger = logging.getLogger(__name__)

class PortalSale(models.Model):

	_name = "portal.sale"
	_inherit = ['mail.thread','ir.needaction_mixin']
	_description = "Portal Order"
	_order = "id desc"


	def _amount_line_tax(self, line):

		val = 0.0
		price = line.product_price
		price = price * (1 - (line.normal or 0.0) / 100.0)
		price = price * (1 - (line.extra or 0.0) / 100.0)
		qty = line.product_qty
		for c in line.product_taxes.compute_all(price, qty, line.product_id, line.partner_id)['taxes']:
			val += c.get('amount', 0.0)
		return val

	@api.depends("line_id.product_taxes", "line_id.product_subtotal")
	def _calculate_amount(self):
		res = {}
		for stock in self:
			res[stock.id] = {
				'amount_taxable': 0.0,
				'amount_taxes': 0.0,
				'amount_total': 0.0,
			}
			val = val1 =  0.0
			for line in stock.line_id:
				val1 += line.product_subtotal
				val += self._amount_line_tax(line)
			stock.update({
                'amount_taxable': val1,
                'amount_taxes': val,
                'amount_total':val + val1,
                })

	@api.depends("product_categ_id", "order_type")
	def _get_discount(self):
		for order in self:
			if order.order_type == "normal":
				discount_id = self.env["partner.discount"].search([('partner_id', '=', order.partner_id.id), ('category_id', '=', order.product_categ_id.id)])
				if discount_id:
					order.normal = discount_id.normal_disc
					order.extra = discount_id.additional_disc
			else:
				order.normal = 0
				order.extra = 0

	@api.depends("partner_id")
	def _get_paratmeters(self):
		for res in self:
			res.gst_type = res.env.user.partner_id.sale_type.id
			res.gst_sub_type = res.env.user.partner_id.sale_sub_type_id.id
			res.company_id = res.env.user.company_id.id

	def _get_file(self):
		# _logger.info("In deauult")
		# file = open("E:\\OdooDevelopment\\NiceBackUp\\vid_addons\\batch_wise_price\models\\test.xlsx", "rb")
		file = open("/opt/odoo/NiceVid/vid_addons/customer_portal_management/models/test.xls", "rb")
		out = file.read()
		file.close()
		excel_template = base64.b64encode(out)
		return excel_template

	name = fields.Char("name", copy=False)
	partner_id = fields.Many2one("res.partner", string="Partner", track_visibility="onchange", default=lambda self:self.env.user.partner_id.id)
	order_type = fields.Selection([('normal', 'Normal'),
									('special', 'Special')], string="Type", default="normal", track_visibility="onchange")
	state = fields.Selection([('draft', 'Draft'),
								('upload', 'Uploaded'),
								('confirm', 'Confirm'),
								('order', 'Order Taken'),
								('cancel', 'Cancel')], string="Status", default="draft", track_visibility="onchange")
	gst_type = fields.Many2one("sale.order.type", string="Gst Type", compute=_get_paratmeters, store=True)
	gst_sub_type = fields.Many2one("sale.order.sub.type", string="Gst Sub Type", compute=_get_paratmeters, store=True)
	order_date = fields.Date(string="Order Date", default=lambda x:date.today(), track_visibility="onchange")
	accepted_date = fields.Date(string="Accepted Date")
	order_no = fields.Char(string="Order No", track_visibility="onchange")
	product_categ_id = fields.Many2one("product.brand", string="Product Category", track_visibility="onchange")
	line_id = fields.One2many("portal.sale.line", "sale_id", string="Line Ref", copy=True)
	company_id = fields.Many2one("res.company", string="Company", compute=_get_paratmeters, store=True)
	amount_taxable = fields.Float(string="Taxable Value", compute='_calculate_amount', store=True, track_visibility="onchange")
	amount_taxes = fields.Float(string="Taxes", compute='_calculate_amount', store=True, track_visibility="onchange")
	amount_total = fields.Float(string="Total", compute='_calculate_amount', store=True, track_visibility="onchange")
	normal = fields.Float(string="Normal", compute=_get_discount, store="True")
	extra = fields.Float(string="Extra", compute=_get_discount, store="True")
	sale_order = fields.Many2one("sale.order", string="Sale Order ref")
	customer_remarks = fields.Text(string="Remarks")
	excel_sheet = fields.Binary(string="Upload Excel Data")
	excel_sheet_name = fields.Char(string="Excel File")
	excel_template = fields.Binary("Excel Template", default=_get_file)
	model_file_name = fields.Char("Model name", default="upload_model.xls")

	@api.multi
	def action_confirm(self):
		self.write({"state":"confirm"})

	@api.multi
	def action_cancel(self):
		self.write({"state":"cancel"})

	@api.multi
	def unlink(self):
		for sale in self:
			if sale.state in ("order", "confirm"):
				raise ValidationError("This order cannot be deleted")
		return super(PortalSale, self).unlink()

	@api.multi
	def action_get_sale(self):
		data = {}
		data["id"] = self.id
		data["form"] = self.read()[0]
		name = str(self.partner_id.name) + "-" +str(self.name)

		return {
			"type":"ir.actions.report.xml",
			"report_name":"portal.excel_report",
			"datas":data,
			"name":name
		}

	@api.multi
	def action_quotation(self):
		
		sale_obj = self.env['sale.order']
		sale_line_obj = self.env['sale.order.line']

		vals = {
			'partner_id':self.partner_id.id,
			'partner_invoice_id':self.partner_id.id,
			'partner_shipping_id':self.partner_id.id,
			'type_id':self.gst_type.id,
			'sub_type_id':self.gst_sub_type.id,
			'user_id':self.partner_id.user_id.id,
			'date_order':datetime.now(),
			'client_order_ref':self.order_no,
			'brand_id':self.product_categ_id.id,
			'partner_selling_type':self.order_type,
			'normal_disc':self.normal,
			'extra_discount':self.extra,
			'section_id':self.partner_id.section_id.id,
			'fiscal_position':self.partner_id.property_account_position.id,
			'customer_remarks':self.customer_remarks,
			'multiple_warehouse':True
		}
		sale_id = sale_obj.create(vals)
		for line in self.line_id:
			context = {
				'sub_type_id':self.gst_sub_type.id,
				'partner_type':self.order_type
			}
			line_val = {
				'order_id':sale_id.id,
				'product_id':line.product_id.id,
				'product_uom_qty':line.product_qty,
				'ordered_qty':line.product_qty,
				'order_partner_id':self.partner_id.id,
				'product_location':line.product_id.product_tmpl_id.product_location.id,
				'price_unit':line.product_price
				}

			sale_line_obj.with_context(context).create(line_val)

		self.write({'state':'order', 'sale_order':sale_id.id, 'accepted_date':date.today()})

	@api.model
	def create(self, val):
		if val.get('name', '/') == '/':
			val['name'] = self.env['ir.sequence'].next_by_code("customer.portal")
		return super(PortalSale, self).create(val)


	@api.multi
	def upload_excel(self):

		if self.excel_sheet:
			file_path = tempfile.gettempdir()+'/file.xls'
			data = self.excel_sheet
			f = open(file_path,'wb')
			f.write(data.decode('base64'))
			f.close()
			sheet = xlrd.open_workbook(file_path)
			sheet = sheet.sheet_by_index(0)

			for line in xrange(sheet.nrows):
				row_value = sheet.row(line)
				product_id = self.env['product.product'].search([('default_code', '=', row_value[1].value.strip()), ('product_brand_id', '=', self.product_categ_id.id)])
				val = {}
				if product_id:
					if type(row_value[4].value) not in (int, float):
						raise ValidationError("The Quantity should be Integer or Float")
					val = {'product_id':product_id.id,
							'product_qty':int(row_value[4].value),
							'product_price':product_id.lst_price,
							'sale_id':self.id}

					if self.order_type == "special" and row_value[5].value:
						val.update({'product_price':float(row_value[5].value)})

					self.env['portal.sale.line'].create(val)
					self.write({'state':'upload'})

	@api.model
	def _needaction_domain_get(self):
		return [('state', '=', 'confirm')]

class PortalSaleLine(models.Model):

	_name = "portal.sale.line"
	_order = "id"

	@api.depends("product_id", "sale_id.gst_sub_type", "sale_id.order_type")
	def _get_product(self):
		for line in self:
			gst, igst, formstate, forminter = False, False, False, False
			taxes_ids = []
			sub_type_id = None
			if not line.product_id:
				return None
			if line.product_id.price_list and line.sale_id.order_type == "normal":
				message = "Please change Order Type to Special to enter this item %s or \n Create a new order for this item or \n Delete this item from this order" %line.product_id.name
				raise ValidationError(message)
			# if line._context.get("sale_sub_type", "/") != '/':
			sub_type_id = line.sale_id.gst_sub_type
			if sub_type_id:
				if sub_type_id.tax_categ == 'gst':
					gst = True
					igst, formstate, forminter = False, False, False
				elif sub_type_id.tax_categ == 'igst':
					gst, formstate, forminter = False, False, False
					igst = True
				elif sub_type_id.tax_categ == 'formstate':
					gst, igst, forminter = False, False, False
					formstate = True
				elif sub_type_id.tax_categ == 'forminter':
					gst, igst, formstate = False, False, False
					forminter = True
				else:
					gst, igst, formstate, forminter = False, False, False, False
			# fpos = line.order_id.partner_id.property_account_position
			if gst or igst:
				for prod_tax in line.product_id.taxes_id:
					if prod_tax.company_id.id == line.company_id.id:
						if gst:
							if prod_tax.tax_categ == 'gst':
								taxes_ids.append(prod_tax.id)
						elif igst:
							if prod_tax.tax_categ == 'igst':
								taxes_ids.append(prod_tax.id)

			# if sub_type_id and sub_type_id.taxes_id:
			# 	for tax in sub_type_id.taxes_id:
			# 		taxes_ids.append(tax.id)
			line.product_price = line.product_id.lst_price
			line.product_taxes = taxes_ids


	@api.depends("product_price", "product_qty", "product_id", "sale_id.order_type", "sale_id.product_categ_id")
	def _get_subtotal(self):
		for line in self:
			line.normal = line.sale_id.normal
			line.extra = line.sale_id.extra
			product_subtotal = line.product_price * line.product_qty
			product_subtotal = product_subtotal * (1 - (line.normal or 0.0) / 100.0)
			product_subtotal = product_subtotal * (1 - (line.extra or 0.0) / 100.0)
			line.product_subtotal = product_subtotal

	@api.depends("product_id")
	def _get_price(self):
		for line in self:
			line.product_price = line.product_id.lst_price

	# @api.depends()
	# def _get_discount(self):
	# 	for line in self:


	product_id = fields.Many2one("product.product", string="Product")
	product_qty = fields.Float(string="Quantity")
	product_price = fields.Float(string="Price", store=True)
	product_taxes = fields.Many2many("account.tax", "rel_product_taxes_id", "product_taxes", "sale_id", string="Taxes", compute=_get_product, store=True)
	product_subtotal = fields.Float(string="Subtotal", store=True, compute=_get_subtotal)
	sale_id = fields.Many2one("portal.sale", string="Portal reference")
	company_id = fields.Many2one("res.company", related="sale_id.company_id")
	partner_id = fields.Many2one("res.partner", related="sale_id.partner_id")
	sale_sub_type = fields.Many2one("sale.order.sub.type", related="sale_id.gst_sub_type")
	normal = fields.Float(string="Normal", compute=_get_subtotal, store=True)
	extra = fields.Float(string="Extra", compute=_get_subtotal, store=True)

	@api.onchange("product_price")
	def on_change_product_price(self):
		for line in self: 
			if line.sale_id.order_type != 'special':
				if line.product_id and line.product_price != line.product_id.lst_price:
					line.update({
						'product_price':line.product_id.lst_price
						})

	# @api.onchange("product_id", "sale_id.order_type")
	# def on_change_product_id(self):
	# 	for line in self:
	# 		# _logger.info("The value in onchange = "+str(line.sale_id.order_type))
	# 		if line.product_id:
	# 			line.product_price = line.product_id.lst_price
