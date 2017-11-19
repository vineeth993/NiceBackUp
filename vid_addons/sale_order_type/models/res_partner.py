# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_type = fields.Many2one(
        comodel_name='sale.order.type', string='Sale Order Type',
        company_dependent=True)
    sale_sub_type_id = fields.Many2many("sale.order.sub.type", "sale_order_sub_type_rel", "partner_id", "type_id", string="Sub Type")
    purchase_type = fields.Many2one('sale.order.type', string="Purchase order type")
    purchase_sub_type_id = fields.Many2many("sale.order.sub.type", "purchase_order_sub_type_rel", "partner_id", "type_id", string="Sub Type")
