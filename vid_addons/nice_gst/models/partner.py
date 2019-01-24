# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class ResPartner(models.Model):
	_inherit = 'res.partner'


	country_base_gst_type = fields.Selection([('national', 'National'), ('international', 'International')], string="GST Type")
	gst_reg = fields.Selection([('registered', 'Registered'), ('unregistered', 'Unregistered'),
								('cs', 'Composite Supplier'),('ngs', 'Non GST Supplier')], string="GST Status", default="registered")
	gst_category = fields.Selection([
	('gst', 'Local'),
	('igst', 'Interstate'),
	], string="GST Category")
	gst_no = fields.Char('GST No', size=64)
	tds_categ = fields.Many2one("tds.category", string="TDS Category")
	reverse_tax_1 = fields.Many2one('reverse.tax')
	gst_credit = fields.Boolean('GST Credit')
	ssi_unit = fields.Boolean('SSI Unit')
	ssi_no = fields.Char("MSME Number")
	pan = fields.Char("PAN")
	supplier = fields.Boolean(string="Supplier", default=True)
	personal_mail = fields.Char(string="Personal Mail")
	drug_lic_no = fields.Char(string="Drug Licence")
	poison_lic_no = fields.Char(string="Poison Licence")

	@api.multi
	def onchange_state(self, state_id=None):
		res = super(ResPartner, self).onchange_state(state_id)
		if state_id and state_id == self.env.user.company_id.state_id.id:
			res['value']['gst_category'] = 'gst'
		elif state_id:
			res['value']['gst_category'] = 'igst'
		return res

class Res(models.Model):
	_inherit = 'res.partner.bank'

	micr = fields.Char('MICR')
	MFGR = fields.Char('MFGR')
	bank_bic = fields.Char("IFSC")

class TDSCategory(models.Model):
	
	_name = "tds.category"

	name = fields.Char("TDS Name", required=True)
	tds_perc = fields.Float("TDS(%)", required=True)

class TDSCategory(models.Model):
	
	_name = "reverse.tax"

	name = fields.Char("Reverse Tax Name", required=True)
	reverse_perc = fields.Float("Reverse tax(%)", required=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: