# -*- coding: utf-8 -*-

{
    'name': 'Sales Report',
    'version': '1.0',
    'author': 'Steigend IT Solutions',
    'category': 'Sales Management',
    'summary': 'Sales Order Status Report',
    'description': '''
  ''',
    'depends': ['sale', 'report_xls'],
    'data': [
        'wizard/sale_report_view.xml',
        'report/sale_report.xml',
        'views/sale_view.xml',
#         'report_view.xml'
    ],
    'installable': True,
    'application': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
