# -*- coding: utf-8 -*-

{
    'name': 'GST',
    'version': '1.0',
    'author': 'Indimedi Solutions Pvt. Ltd',
    'category': 'Accounting',
    'summary': 'GST enabled Customizations',
    'description': '''
  ''',
    'depends': ['sale', 'account', 'purchase','nice_gst','sale_customization'],
    'data': [
        'views/gst_refund_reason.xml',
        'views/account_invoice_view.xml'
    ],
    'installable': True,
    'application': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
 