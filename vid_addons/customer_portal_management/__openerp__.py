# -*- coding: utf-8 -*-
{
    'name': "Customer Portal Management",

    'summary': """
    """,

    'description': """
    """,

    'author': "VIDTS",
    'website': "http://www.vidts.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Portal',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','portal','portal_sale', 'web'],

    # always loaded
    'data': [
        'wizard/confirm_order_view.xml',
        'views/portal_sale_view.xml',
        'views/sale_menu_view.xml',
        'views/portal_menu.xml',
        'views/portal_price_list.xml',
        'views/base_view.xml',
        'report/report_portal_sale.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/rules.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'application':True
}
