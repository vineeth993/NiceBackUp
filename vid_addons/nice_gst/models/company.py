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
    ref = fields.Char("Refernce", required=True, size=7)

    def create(self, cr, uid, vals, context):
        if not vals.get('name', False) or vals.get('partner_id', False):
            self.cache_restart(cr)
            return super(ResCompany, self).create(cr, uid, vals, context=context)
        obj_partner = self.pool.get('res.partner')
        partner_id = obj_partner.create(cr, uid, {
            'name': vals['name'],
            'is_company': True,
            'image': vals.get('logo', False),
            'customer': False,
            'email': vals.get('email'),
            'phone': vals.get('phone'),
            'website': vals.get('website'),
            'vat': vals.get('vat'),
            'ref': vals.get('ref')
        }, context=context)
        vals.update({'partner_id': partner_id})
        self.cache_restart(cr)
        company_id = super(ResCompany, self).create(cr, uid, vals, context=context)
        obj_partner.write(cr, uid, [partner_id], {'company_id': company_id}, context=context)
        return company_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: