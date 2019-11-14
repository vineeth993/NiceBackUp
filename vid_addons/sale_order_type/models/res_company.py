from openerp import fields, api, _, models

class ResCompany(models.Model):

	_inherit = "res.company"

	is_multi_warehouse = fields.Boolean(string="Has Multi Warehouse")