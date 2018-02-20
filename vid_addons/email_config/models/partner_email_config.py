
from openerp import fields, api, models, _
from openerp.exceptions import ValidationError 

from openerp.osv import osv
from openerp.tools.translate import _
from openerp.tools import html2text
import openerp.tools as tools

import logging 

_logger = logging.getLogger(__name__)

class PartnerEmail(models.Model):

	_inherit = 'hr.employee'

	email_config_id = fields.Many2one('ir.mail_server', 'Config Id')
	password = fields.Char("Password")
	smtp_encryption = fields.Selection([('none', 'None'),
										('starttls','TLS (STARTTLS)'),
                                        ('ssl','SSL/TLS')],
                                        string="Connection Security", default='ssl')
	smtp_server = fields.Many2one("smtp.config", string="Server")

	@api.model
	def create(self, value, context=None):
		ir_server = self.env['ir.mail_server']
		email = ir_server.search([('smtp_user', '=', value['work_email'])])
		smtp_config = self.env['smtp.config'].browse(value['smtp_server'])
		if email.id:
			raise ValidationError("Email Already Exist")
		val = {'name':value['name'],
				'smtp_host':smtp_config.smtp_server,
				'smtp_port':smtp_config.smtp_port,
				'smtp_encryption':value['smtp_encryption'],
				'smtp_user':value['work_email'],
				'smtp_pass':value['password']
				}
		config_id = ir_server.create(val)
		value['email_config_id'] = config_id.id
		return super(PartnerEmail, self).create(value, context=context)

	@api.multi
	def write(self, value):
		# _logger.info("The Value in write = "+str(value))
		val = {}
		if value.has_key('work_email'):
			val['smtp_user'] = value['work_email']
		if value.has_key('password'):
			val['smtp_pass'] = value['password']
		if value.has_key('smtp_encryption'):
			val['smtp_encryption'] = value['smtp_encryption']
		if value.has_key('smtp_server'):
			smtp_config = self.env['smtp.config'].browse(value['smtp_server'])
			val['smtp_host'] = smtp_config.smtp_server
			val['smtp_port'] = smtp_config.smtp_port
		if val:
			employee_id = self.browse(self.id)
			# _logger.info("The employee id = "+str(employee_id))
			server_conf = self.env['ir.mail_server']
			if employee_id.email_config_id:
				ir_server = server_conf.browse(employee_id.email_config_id.id)
				ir_server.write(val)
			else:
				if not val.has_key('smtp_user'):
					val['smtp_user'] = employee_id.work_email
				val['name'] = employee_id.name
				email_id = server_conf.create(val)
				value['email_config_id'] = email_id.id
		return super(PartnerEmail, self).write(value)

	@api.multi
	def smtp_test(self):
		ir_server = self.env['ir.mail_server']
		try:
			connection = ir_server.connect(self.smtp_server.smtp_server, self.smtp_server.smtp_port, 
												user=self.work_email, password=self.password, encryption=self.smtp_encryption)
		except Exception, e:
			raise osv.except_osv(_("Connection Test Failed!"), _("Here is what we got instead:\n %s") % tools.ustr(e))
		finally:
			try:
				if connection: connection.quit()
			except Exception:
				pass
		raise osv.except_osv(_("Connection Test Succeeded!"), _("Everything seems properly set up!"))
