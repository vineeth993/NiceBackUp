
from openerp import fields, api, models, _


class account_config(models.Model):

	_inherit = "account.config.settings"

	round_off = fields.Boolean(string="Round off Invoice Total", default=True)
	round_off_account = fields.Many2one("account.account", string="Round off Account")


	@api.multi
	def set_round_off(self):
		ir_values_obj = self.env['ir.values']
		ir_values_obj.sudo().set_default('account.config.settings', "round_off", self.round_off)
		ir_values_obj.sudo().set_default('account.config.settings', "round_off_account", self.round_off_account.id)