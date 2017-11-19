# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.tools import amount_to_text_en

REFUND_TYPES = [
    ('sale_return', 'Sale Return'),
    ('non_sale_return', 'Non-Sale Return')
    ]

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    gst_refund_type = fields.Selection(REFUND_TYPES, 'Refund Type')
    refund_reason_id = fields.Many2one('gst.refund.reason','Reason for Refund')
    
    @api.multi
    @api.returns('self')
    def refund(self, date=None, period_id=None, description=None, journal_id=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(invoice, date=date, period_id=period_id,
                                    description=description, journal_id=journal_id)
            new_invoices += self.create(values)
        return new_invoices
    
    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        res =  super(AccountInvoice, self)._prepare_refund(invoice, date, period_id, description, journal_id)
        
        if self._context.get('partner_selling_type') and self._context['partner_selling_type']:
            res.update({
                'partner_selling_type':self._context.get('partner_selling_type') or None,
                })
        
        if self._context.get('partner_selling_type_id') and self._context['partner_selling_type_id']:
            res.update({
                'partner_selling_type_id':self._context.get('partner_selling_type_id').id or None,
                })
        
        if self._context.get('extra_discount') and self._context['extra_discount']:
            res.update({
                'extra_discount':self._context.get('extra_discount') or None,
                })
        
        if self._context.get('additional_extra_disocunt') and self._context['additional_extra_disocunt']:
            res.update({
                'additional_extra_disocunt':self._context.get('additional_extra_disocunt') or None,
                })
            
        if self._context.get('gst_refund_type') and self._context['gst_refund_type']:
            res.update({
                'gst_refund_type':self._context.get('gst_refund_type') or None,
                })
            
        if self._context.get('refund_reason_id') and self._context['refund_reason_id']:
            res.update({
                'refund_reason_id':self._context.get('refund_reason_id').id or None,
                })      
            
        return res