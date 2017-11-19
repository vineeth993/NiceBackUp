# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class ResPartner(models.Model):
    _inherit = 'res.partner'

    country_base_gst_type = fields.Selection([('national', 'National'), ('international', 'International')], string="GST Type")
    gst_reg = fields.Selection([('registered', 'Registered'), ('unregistered', 'Not Registered')], string="GST Registered")
    gst_category = fields.Selection([
    ('gst', 'Local'),
    ('igst', 'Interstate'),
    ], string="GST Category")
    gst_no = fields.Char('GST No', size=64)
    p_code = fields.Char('PCODE')
    tds = fields.Integer('TDS')
    reverse_tax = fields.Integer('Reverse Tax')
    gst_credit = fields.Boolean('GST Credit')
    ssi_unit = fields.Boolean('SSI Unit')
    pan = fields.Char("PAN")
    tax_exempted = fields.Boolean("TAX Exempted")
    deemed_export = fields.Boolean("Deemed Export")
    sez = fields.Boolean("SEZ") 
    export = fields.Boolean("Export")


    @api.multi
    def onchange_state(self, state_id=None):
        res = super(ResPartner, self).onchange_state(state_id)
        if state_id and state_id == self.env.user.company_id.state_id.id:
            res['value']['gst_category'] = 'gst'
        elif state_id:
            res['value']['gst_category'] = 'igst'
        return res

    @api.one
    @api.constrains('sez', 'deemed_export')
    def onchange_sez(self):
        if self.sez and self.deemed_export:
            raise Warning(_('You cannot select both SEZ and Deemed Export'))


    @api.onchange('gst_no', 'country_id')
    def onchange_gst_no(self):
        if self.gst_no:
            self.gst_reg = 'registered'
            self.sez = True
        else:
            self.gst_reg = 'unregistered'
            self.sez = False

        if self.country_id == self.company_id.country_id:
            self.country_base_gst_type = 'national'
            self.export = False
        elif self.country_id:
            self.country_base_gst_type = 'international'
            self.export = True
        if self.state_id and self.state_id == self.company_id.state_id:
            self.gst_category = 'gst'
        elif self.state_id and self.state_id != self.company_id.state_id:
            self.gst_category = 'igst'


class Res(models.Model):
    _inherit = 'res.partner.bank'

    micr = fields.Char('MICR')
    MFGR = fields.Char('MFGR')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: