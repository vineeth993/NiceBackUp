# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import fields, models, api


class ResPartner(models.Model):
	_inherit = 'res.partner'

	sale_type = fields.Many2one(comodel_name='sale.order.type', string='Sale Order Type', track_visibility='onchange')
	sale_sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type", track_visibility='onchange')
	purchase_type = fields.Many2one('sale.order.type', string="Purchase order type")
	purchase_sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type")