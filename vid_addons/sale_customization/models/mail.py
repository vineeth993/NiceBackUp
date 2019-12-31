
from openerp import fields, models, api, SUPERUSER_ID, _
from email.header import decode_header
from email.utils import formataddr
import logging


_logger = logging.getLogger(__name__)

class MailMessage(models.Model):

	_inherit = 'mail.message'

	def _get_default_from(self, cr, uid, context=None):
		this = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
		if this.alias_name and this.alias_domain:
			return formataddr((this.name, '%s@%s' % (this.alias_name, this.alias_domain)))
		elif this.email:
			return this.email
		raise osv.except_osv(_('Invalid Action!'), _("Unable to send email, please configure the sender's email address or alias."))

