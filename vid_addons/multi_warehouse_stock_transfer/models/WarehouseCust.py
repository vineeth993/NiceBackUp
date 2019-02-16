
from openerp import fields, api, models, _
from openerp.exceptions import ValidationError

class Warehouse(models.Model):

	_inherit = "stock.warehouse"

	dc_seq = fields.Many2one('ir.sequence', string="DC Sequence")
	issue_seq = fields.Many2one('ir.sequence', string="Issue Sequence")
	request_seq = fields.Many2one('ir.sequence', string="Request Sequence")