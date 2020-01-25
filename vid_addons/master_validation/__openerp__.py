# -*- coding: utf-8 -*-
{
    'name': "Master Validation",

    'author': "VIDTS",
    'website': "http://www.vidts.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Master',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'purchase', 'sale', 'crm', 'report', 'mail', 'product'],

    # always loaded
    'data': [
        'report/report.xml',
        'security/security.xml',
        'views/partner_cust.xml',
        'views/purchase.xml',
        'views/sale.xml',
        'views/invoice.xml',
        'views/partner_report.xml',
        'views/product_cust.xml',
        'data/master_validation_template.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],

    'application':True
}
