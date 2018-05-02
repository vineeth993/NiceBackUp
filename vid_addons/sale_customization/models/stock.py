# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        partner, currency_id, company_id, user_id = key
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        return {
            'origin': move.picking_id.name,
            'date_invoice': context.get('date_inv', False),
            'user_id': user_id,
            'partner_id': partner.id,
            'account_id': account_id,
            'payment_term': payment_term,
            'type': inv_type,
            'fiscal_position': partner.property_account_position.id,
            'company_id': company_id,
            'currency_id': currency_id,
            'journal_id': journal_id,
            'partner_selling_type':move.picking_id.sale_id.partner_selling_type,
            'normal_disc':move.picking_id.sale_id.normal_disc,
            'extra_discount':move.picking_id.sale_id.extra_discount,
            'nonread_extra_disocunt':move.picking_id.sale_id.nonread_extra_disocunt,
            'nonread_normal_disocunt':move.picking_id.sale_id.nonread_normal_disocunt,
            'sale_order':move.picking_id.sale_id.name
        }
    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Forbbiden to duplicate'), _('Is not possible to duplicate the record, please create a new one.'))



class stock_move(osv.osv):

    _inherit = "stock.move"
    _order = 'name, product_id, date_expected desc, id'

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        if inv_type in ('out_invoice', 'out_refund') and move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id
            res['additional_discount'] = sale_line.additional_discount
        return res
