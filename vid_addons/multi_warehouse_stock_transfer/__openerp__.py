# -*- coding: utf-8 -*-
{
    'name': "Multi Warehouse Stock Transfer",

    'summary': """
        Sock Transfer between multi company""",

    'description': """
    """,

    'author': "VIDTS",
    'website': "http://www.vidts.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Mutli Company',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','report','product'],

    # always loaded
    'data': [
        'wizard/getEWP_view.xml',
        'wizard/stock_cancel.xml',
        'report/report.xml',
        'views/Warehouse_cust_view.xml',
        'views/stockRequest_view.xml',
        'views/stockIssue_view.xml',
        'views/stock_view.xml',
        'views/dc_view.xml',
        'views/report_dc.xml',
        'views/users.xml',
        'views/product_view.xml',
        'data/transfer_multi_warehouse.xml',
        'security/ir.model.access.csv'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'application':True
}
