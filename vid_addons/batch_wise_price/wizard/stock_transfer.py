from openerp import fields, api, models, _
from openerp.exceptions import ValidationError

import logging

class StockTransfer(models.TransientModel):

	_inherit = 'stock.transfer_details_items'

	pricelist_id = fields.Many2one("product.batch.pricelist", string="Year Wise Price", readonly="True")