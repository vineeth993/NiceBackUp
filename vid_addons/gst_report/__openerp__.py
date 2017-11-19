# -*- coding: utf-8 -*-
{
    'name': "GST FILING",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','report_xls', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/hsn_report.xml',
        'wizard/B2B_sale_report.xml',
        'report/hsn_summary_report.xml',
        'report/b2b_summary_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],

    'application':True
}