
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PartnerCust(models.Model):

	_inherit = "res.partner"

	state = fields.Selection([('draft', 'Draft'),
							  ('confirm', 'Confirm'),
							  ('validate', 'Validate'),
							  ('approve', 'Approved')], string="State", default="draft", track_visibility="onchange")
	confirmed_user = fields.Many2one("res.users", string="Confirmed User")

	@api.multi
	def write(self, vals):
		if self.state == "approve" and self.env.context.get('make_readonly') and vals.get('message_last_post', '/') == '/' and self.is_company and vals.get('credit', '/') == '==':
			raise ValidationError("Document is approved cannot be edited please contact administrator")
		elif self.state == "approve" and self.env.context.get('make_readonly', 1) == 1  and vals.get('message_last_post', '/') == '/' and self.is_company  and vals.get('credit', '/') == '==':
			raise ValidationError("Document is approved cannot be edited please contact administrator")
		res = super(PartnerCust, self).write(vals)
		return res

	@api.multi
	def reset_to_draft(self):
		self.update({'state':'draft'})

	@api.multi
	def action_confirm(self):
		self.update({'state':'confirm', 'confirmed_user':self.env.user})

	@api.multi
	def action_validate(self):
		# if self.env.user == self.confirmed_user:
		# 	raise ValidationError("User who confirmed doesn't have permission to validate this document")
		self.update({'state':'validate'})

	@api.multi
	def action_approve(self):
		self.update({'state':'approve'})

	@api.multi
	def admin_reset(self):
		self.update({'state':'draft'})

	@api.multi
	def action_mail(self):

		mail_wizard_id = self.env.ref('mail.email_compose_message_wizard_form')
		template_id = self.env.ref('master_validation.master_validation_template')
		ctx = dict()
		if template_id:
			ctx.update({
				'default_model':'res.partner',
				'default_res_id':self.id,
				'default_use_template': bool(template_id),
				'default_template_id': template_id.id,
				'default_composition_mode': 'comment',
				'mark_so_as_sent': True,
				})

		return{
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'res_model':'mail.compose.message',
			'views':[(mail_wizard_id.id, 'form')],
			'view_id':mail_wizard_id.id,
			'target':'new',
			'context':ctx
		}
