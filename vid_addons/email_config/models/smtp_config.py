
from openerp import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class SmtpConfig(models.Model):

	_name = "smtp.config"

	name = fields.Char(string="Mail", required=True)
	smtp_server = fields.Char(string="SMTP Server", required=True)
	smtp_port = fields.Integer(string="SMTP Port", size=5, required=True)

