# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'order_id desc, sequence, id'
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(SaleOrderLine, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, 
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, 
            fiscal_position=fiscal_position, flag=flag, context=context)
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        context_partner.update({'lang': lang, 'partner_id': partner_id})
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)
        tax_ids = []
        gst, igst = False, False
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        company_gst = company.gst_no and company.gst_no[:2] or ''
        partner_gst = partner.gst_no and partner.gst_no[:2] or ''
        if company_gst and partner_gst:
            if company_gst == partner_gst:
                gst = True
            else:
                igst = True
        else:
            gst = True
        for tax in product_obj.taxes_id:
            if tax.company_id.id == company.id:
                if gst:
                    if tax.tax_categ == 'gst':
                        tax_ids.append(tax.id)
                elif igst:
                    if tax.tax_categ == 'igst':
                        tax_ids.append(tax.id)
        res['value']['tax_id'] = tax_ids
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: