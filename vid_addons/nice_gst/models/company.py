# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    gst_no = fields.Char('GST No', size=64)
    letter_head_ok = fields.Boolean('Print in Letter Head', default=False)
    cin = fields.Char("CIN")
    tin = fields.Char("TIN")
    cst = fields.Char("CST")
    ce_regn_no = fields.Char("CE Regn No")
    range_div = fields.Char("Range & Division")
    poison_lic_no = fields.Char("Poison Lic.No")
    drug_mfg_lic_no = fields.Char("Drug Mfg.Lic.No")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: