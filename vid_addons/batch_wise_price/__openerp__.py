# -*- coding: utf-8 -*-
{
    'name': "Year Wise Price List",

    'summary': """
        Year Wise Price list""",

    'description': """
    """,

    'author': "VIDTS",
    'website': "http://www.vidts.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'List Price',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock_account', 'account', 'product'],

    # always loaded
    'data': [
        'views/account_invoice.xml',
        'views/product_view.xml',
        'views/lot_serial_view.xml',
        'wizard/stock_change_product_qty_view.xml',
        'wizard/stock_transfer_details_custom2.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'application':True
}