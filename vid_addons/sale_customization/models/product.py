from openerp import models, fields, api, _, tools

# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2009-2015 Noviat (http://www.noviat.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Luc de Meyer <info@noviat.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class HSCode(models.Model):
	_name = "hs.code"
	_description = "HS Code"
	_order = "code"
	_rec_name = "code"

	code = fields.Char('H.S. Code', required=True)
	description = fields.Char('Description', required=True)

	@api.model
	def create(self, vals):
		if vals.get('code'):
			vals['code'] = vals['code'].replace(' ', '')
		return super(HSCode, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('code'):
			vals['code'] = vals['code'].replace(' ', '')
		return super(HSCode, self).write(vals)

	@api.one
	@api.constrains('code')
	def check_hsn(self):
		hsn_id = None
		if self.code:
			hsn_id = self.search([('code', '=', self.code)])
			if len(hsn_id) > 1:
				raise ValidationError('Hsn number already in use')

class ProductProduct(models.Model):
	_inherit = 'product.product'

	hazard_type = fields.Selection([(1, 'Hazard'), (2, 'Non Hazard')])
	control_type = fields.Selection([(1, 'Controlled'), (2, 'Non Controlled')])
	gcode = fields.Char('Product Gcode')
	cas_no = fields.Char(string='CAS No')
	profiling_seasons = fields.Many2many('sale.reason', 'product_template_sale_reason_rel',
										 'product_template_id', 'sale_reason_id',
										 string='Profiling Season')
	default_code = fields.Char(string='Product Code', select=True)
	uom_id_one = fields.Many2one('product.uom', 'Unit')
	uom_id_two = fields.Many2one('product.uom', 'Unit')
	uom_id_three = fields.Many2one('product.uom', 'Unit')
	uom_id_pack = fields.Many2one('product.pack', 'Packed in')
	specific_gravity = fields.Float(string="Specific Gravity")
	schedule = fields.Many2one('product.schedule', 'Schedule')
	grade = fields.Many2one('product.grade', string="Grade")
	price_list = fields.Boolean("Special")
	case_lot = fields.Float('Case Lot')

	_defaults = {
		'type': 'product',
	}

	@api.one
	@api.constrains('default_code')
	def _check_default_code(self):
		if self.default_code:
			names = self.search([('default_code', '=', self.default_code)])
			if len(names) > 1:
				raise Warning('A product with the same Internal Reference(Product Code) already exists')


class ProductSchedule(models.Model):
	_name = 'product.schedule'

	name = fields.Char("Number")
	tax_id = fields.Many2one('account.tax', string="Related Tax")


class ProductPack(models.Model):
	_name = 'product.pack'

	name = fields.Char("Pack Type")


class ProductGrade(models.Model):
	_name = 'product.grade'

	name = fields.Char("Grade Name")
	
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends("taxes_id")
    def _get_tax(self):
        for line in self:
            for tax in line.taxes_id:
                if tax.gst_type == "igst":
                    line.product_tax = tax.amount * 100
                    return 

    hazard_type = fields.Selection([(1, 'Hazard'), (2, 'Non Hazard')])
    control_type = fields.Selection([(1, 'Controlled'), (2, 'Non Controlled')])
    gcode = fields.Char('Product Gcode')
    cas_no = fields.Char(related='product_variant_ids.cas_no', string='CAS No')
    profiling_seasons = fields.Many2many('sale.reason', 'product_template_sale_reason_rel',
                                         'product_template_id', 'sale_reason_id',
                                         string='Profiling Season')
    default_code = fields.Char(related='product_variant_ids.default_code', string='Product Code')
    uom_id_one = fields.Many2one('product.uom', 'Unit')
    uom_id_two = fields.Many2one('product.uom', 'Unit')
    uom_id_three = fields.Many2one('product.uom', 'Unit')
    uom_id_pack = fields.Many2one('product.pack', 'Packed in')
    certificate_of_analysis = fields.Boolean(string="Certificate of analysis")
    grade = fields.Many2one('product.grade', string="Grade")
    hs_code_id = fields.Many2one('hs.code', 'H.S.Code', required=True)
    price_list = fields.Boolean(related='product_variant_ids.price_list', string="Non Pricelist Item")
    case_lot = fields.Float(related='product_variant_ids.case_lot', string="Case Lot")
    input_tax_credit = fields.Boolean(related='product_variant_ids.input_tax_credit', string='Input Tax Credit')
    expected_loss = fields.Float(related='product_variant_ids.expected_loss', string='Expected Loss %')

    product_group_id = fields.Many2one("product.product", string="Product Group", domain=[('product_group', '=', True)])
    product_group = fields.Boolean(related='product_variant_ids.product_group', string="Grouping Product")
    product_tax = fields.Float(string="Product Tax(%)", compute="_get_tax", store=True)

    _defaults = {
        'type': 'product',
        }

	@api.one
	@api.constrains('name')
	def _check_name(self):
		if self.name:
			names1 = self.search([('name', '=', self.name)])
			if len(names1) > 1:
				raise Warning('A product with the same Name already exists')
