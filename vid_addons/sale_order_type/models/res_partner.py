# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
	_inherit = 'res.partner'

	@api.depends('sale_sub_type_id')
	def _get_form_sale(self):
		for partner in self:
			if partner.sale_sub_type_id:
				if partner.sale_sub_type_id.tax_categ == 'formstate' or partner.sale_sub_type_id.tax_categ == 'forminter':
					partner.form_sale = True
				else:
					partner.form_sale = False

	sale_type = fields.Many2one(comodel_name='sale.order.type', string='Sale Order Type', track_visibility='onchange')
	sale_sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type", track_visibility='onchange')
	purchase_type = fields.Many2one('sale.order.type', string="Purchase order type")
	purchase_sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type")
	form_sale = fields.Boolean("Form Sale", compute="_get_form_sale")

	@api.multi
	@api.onchange('purchase_type', 'sale_type')
	def on_change_type(self):
		if self.purchase_type or self.sale_type:
			self.is_company = True
		else:
			self.is_company = False