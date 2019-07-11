
from openerp import models, fields, api, _

class AccountInvoice(models.Model):

	_inherit = "account.invoice.line"

	lot_id = fields.Many2one("stock.production.lot", string="Batch No")