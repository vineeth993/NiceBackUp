# -*- coding: utf-8 -*-

{
    'name': 'Sales Management',
    'version': '1.0',
    'author': 'Steigend IT Solutions',
    'category': 'Sales Management',
    'description': '''
CRM/Sales Customization
  ''',
    'depends': ['base', 'crm', 'sale', 'sale_stock', 'purchase', 'product', 'stock_account', 'mrp', 'fleet'],
    'data': [
        'views/lead_view.xml',
        'views/partner_selling_type_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/account_view.xml',
#         'security/ir.model.access.csv',
        'views/base_view.xml',
    ],
    'installable': True,
    'auto_install': False

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
