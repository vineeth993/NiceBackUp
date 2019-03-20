
from openerp import fields, models, api, _

class ResUser(models.Model):

	_inherit = "res.users"

	related_warehouse_id = fields.Many2many("stock.warehouse", "warehouse_user_rel", "warehouse_id", "user_id", string="Warehouse")