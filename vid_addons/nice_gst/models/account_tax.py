# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

TAX_TYPES = [
    ('gst', 'Local GST'),
    ('igst', 'Interstate GST'),
    ('none', 'None'),
    ]
GST_TYPES = [
    ('cgst', 'CGST'),
    ('sgst', 'SGST'),
    ('igst', 'IGST')
    ]
class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    tax_categ = fields.Selection(TAX_TYPES, 'Tax Category')
    
class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_categ = fields.Selection(TAX_TYPES, 'Tax Category')
    gst_type = fields.Selection(GST_TYPES, 'GST Type')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: