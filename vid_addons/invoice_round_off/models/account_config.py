
from openerp import fields, api, models, _


class account_config(models.Model):

	_inherit = "res.company"

	round_off = fields.Boolean(string="Round off Invoice Total", default=True)
	round_off_account = fields.Many2one("account.account", string="Round off Account")

