
from openerp.osv import fields, osv
from openerp.tools import email_split
from openerp import SUPERUSER_ID

class  WizardCust(osv.osv_memory):

	_inherit = 'portal.wizard.user'


	def action_apply(self, cr, uid, ids, context=None):
		self.pool['res.partner'].check_access_rights(cr, uid, 'write')
		error_msg = self.get_error_messages(cr, uid, ids, context=context)
		if error_msg:
			raise osv.except_osv(_('Contacts Error'), "\n\n".join(error_msg))

		for wizard_user in self.browse(cr, SUPERUSER_ID, ids, context):
			portal = wizard_user.wizard_id.portal_id
			if not portal.is_portal:
				raise osv.except_osv("Error", "Not a portal: " + portal.name)
			user = self._retrieve_user(cr, SUPERUSER_ID, wizard_user, context)
			# if wizard_user.partner_id.email != wizard_user.email:
			# 	wizard_user.partner_id.write({'email': wizard_user.email})
			if wizard_user.in_portal:
				# create a user if necessary, and make sure it is in the portal group
				if not user:
					user = self._create_user(cr, SUPERUSER_ID, wizard_user, context)
				if (not user.active) or (portal not in user.groups_id):
					user.write({'active': True, 'groups_id': [(4, portal.id)]})
					# prepare for the signup process
					user.partner_id.signup_prepare()
					self._send_email(cr, uid, wizard_user, context)
				wizard_user.refresh()
			else:
				# remove the user (if it exists) from the portal group
				if user and (portal in user.groups_id):
					# if user belongs to portal only, deactivate it
					if len(user.groups_id) <= 1:
						user.write({'groups_id': [(3, portal.id)], 'active': False})
					else:
						user.write({'groups_id': [(3, portal.id)]})
