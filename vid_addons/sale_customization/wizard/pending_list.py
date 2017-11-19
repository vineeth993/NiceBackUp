from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning


class sale_order_pending(models.TransientModel):

	_name="sale.order.pending"

	pending_id = fields.Many2many("sale.order.line","pending_list","pending_id","Pending List")