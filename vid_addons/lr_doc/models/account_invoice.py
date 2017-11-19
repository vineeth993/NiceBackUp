
from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning
import logging


class AccountInvoice(models.Model):

	_inherit = "account.invoice"

	dispatch_id = fields.Char("Dispatch Document", readonly=True)
	docket_number = fields.Char("Docket Number", readonly=True)
	docket_date = fields.Char("Docket Date", readonly=True)
	dispatch_type = fields.Char("Dispatch type", readonly=True)
	courier_name = fields.Char("Courier", readonly=True)
	licence_number = fields.Char("Licence Number", readonly=True)
	driver_name = fields.Char("Name", readonly=True)
	contact_number = fields.Char("Contact No", readonly=True)
	port_id = fields.Many2one("port.code", String="Port Code", readonly=True)