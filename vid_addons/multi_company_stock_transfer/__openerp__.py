# -*- coding: utf-8 -*-
{
    'name': "Multi Company Stock Transfer",

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
    'depends': ['base','stock','report'],

    # always loaded
    'data': [
        'wizard/getEWP_view.xml',
        'views/multi_stock_transfer.xml',
        'views/multi_stock_transfer_outwards.xml',
        'views/stock.xml',
        'data/transfer_multicompany.xml',
        'data/transfer_sequence.xml',
        'security/ir.model.access.csv',
        'report/report.xml',
        'views/report_dc.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'application':True
}