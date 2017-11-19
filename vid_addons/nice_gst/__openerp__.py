# -*- coding: utf-8 -*-

{
    'name': 'GST',
    'version': '1.0',
    'author': 'Steigend IT Solutions',
    'category': 'Purchase Management',
    'summary': 'GST enabled Customizations',
    'description': '''
  ''',
    'depends': ['sale', 'account', 'purchase'],
    'data': [
        'views/partner_view.xml',
        'views/company_view.xml',
        'views/account_tax_view.xml',
        'views/report_invoice_gst.xml',
        'views/account_invoice_view.xml'
    ],
    'installable': True,
    'application': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
 