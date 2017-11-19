# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        res = super(PurchaseOrderLine, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned, name=name, price_unit=price_unit, 
            state=state, context=context)
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        if partner_id:
            lang = partner.lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_obj.browse(cr, uid, product_id, context=context_partner)
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
        for tax in product.supplier_taxes_id:
            if tax.company_id.id == company.id:
                if gst:
                    if tax.tax_categ == 'gst':
                        tax_ids.append(tax.id)
                elif igst:
                    if tax.tax_categ == 'igst':
                        tax_ids.append(tax.id)
        res['value']['taxes_id'] = tax_ids
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: