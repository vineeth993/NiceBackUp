
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import datetime
import logging
import base64
import xlrd
import tempfile
from datetime import date

_logger = logging.getLogger(__name__)

class ProductPrice(models.Model):

	_name = "product.price"
	_order = "id desc"

	pricelist = fields.Many2one("product.batch.pricelist", string="Price List", ondelete="cascade")
	cost = fields.Float("List Price")
	product_id = fields.Many2one("product.product", string="Reference")

	@api.one
	@api.constrains('pricelist')
	def check_year(self):
		hsn_id = None
		if self.pricelist:
			hsn_id = self.search([('pricelist', '=', self.pricelist.id), ('product_id', '=', self.product_id.id)])
			if len(hsn_id) > 1:
				raise ValidationError('Single pricelist for a year')

class ProductTemplate(models.Model):

	_inherit = "product.product"

	price_id = fields.One2many("product.price", "product_id", string="Reference")

class ProductProduct(models.Model):

	_inherit = "product.template"

	price_id = fields.One2many("product.price", "product_id", related="product_variant_ids.price_id", string="Reference")


class PriceList(models.Model):

	_name = "product.batch.pricelist"
	_inherit = ['mail.thread']
	_description = "Batch Wise price"
	_order = "id desc"

	def _get_file(self):
		# _logger.info("In deauult")
		#file = open("E:\\OdooDevelopment\\NiceBackUp\\vid_addons\\batch_wise_price\models\\test.xlsx", "rb")
		file = open("/opt/odoo/NiceVid/vid_addons/batch_wise_price/models/test.xlsx", "rb")
		out = file.read()
		file.close()
		excel_model = base64.b64encode(out)
		return excel_model

	name = fields.Char(string="Name", compute="_get_name", store=True, track_visibility="onchange")
	date_effective = fields.Date(string="Date Effectice", default=lambda x: date.today())
	description = fields.Text(string="Description")
	price_ids = fields.One2many("product.price", "pricelist", track_visibility="onchange")
	mass_upload = fields.Binary("Load From Excel File")		
	file_name = fields.Char("File name")
	excel_model = fields.Binary("Excel Template", default=_get_file)
	model_file_name = fields.Char("Model name", default="pricelist.xlsx")
	state = fields.Selection([('draft', 'Draft'),
							  ('validate', 'Validate'),
							  ('done', 'Done')], string="State", default="draft", track_visibility="onchange")

	@api.multi
	def unlink(self):
		for price in self:
			if price.state == 'done':
				raise ValidationError("Cannot delete the record")
		return super(PriceList, self).unlink()

	@api.depends('date_effective')
	def _get_name(self):
		trans_date = datetime.strptime(self.date_effective, "%Y-%m-%d").strftime("%d/%m/%Y")
		self.name = "Price list wef : "+str(trans_date)

	@api.one
	@api.constrains('name')
	def check_name(self):
		id = None
		if self.name:
			id = self.search([('name', '=', self.name)])
			if len(id) > 1:
				raise ValidationError('Price list name already exist')

	@api.multi
	def action_validate(self):

		if self.mass_upload:
			file_path = tempfile.gettempdir()+'/file.xlsx'
			data = self.mass_upload
			f = open(file_path,'wb')
			f.write(data.decode('base64'))
			f.close()
			sheet = xlrd.open_workbook(file_path)
			sheet = sheet.sheet_by_index(0)
			line_ids = []
			price_obj = self.env['product.price']	

			for row_no in xrange(sheet.nrows):
				row_value = sheet.row(row_no)
				product_id = self.env["product.product"].search([('default_code', '=', row_value[0].value)])
				if product_id and row_value[3].value:
					val = {
						'pricelist':self.id,
						'product_id':product_id.id,
						'cost':row_value[3].value
						}
					test = price_obj.create(val)
		self.write({'state':'validate'})

	@api.multi
	def action_done(self):

		self.write({"state":'done'})
