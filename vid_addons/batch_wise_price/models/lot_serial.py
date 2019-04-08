 
from openerp import fields, api, models, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class LotSerial(models.Model):
	
	_inherit = "stock.production.lot"

	name = fields.Char('Batch Number', required=True, help="Unique Serial Number")
	pricelist = fields.Many2one('product.batch.pricelist', string="Pricelist")

	@api.onchange('product_id')
	def on_change_product(self):

		if self.product_id:
			get_pricelist = self.env['product.batch.pricelist'].search([('price_ids.product_id', '=', self.product_id.id)])
			if get_pricelist:
				value = min(get_pricelist)
				self.pricelist = value.id

				