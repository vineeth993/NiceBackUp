# -*- coding: utf-8 -*-
# Part of Abdallah Mohammed (<abdalla_mohammed@outlook.com>). See LICENSE file for full copyright and licensing details.

{
    'name': 'Chemical ERP Reports',
    'version': '1.0',
    'author': 'VIDTS Techno',
    'license': 'Other proprietary',
    'category': 'report',
    'depends': ['base', 'sale', 'stock', 'delivery'],
    'data': [
        'report.xml',
        'report/sale_order_report.xml',
        'report/stock_picking_report.xml',
        'report/sale_stock_report.xml'
    ],
    'installable': True,
    'auto_install': False

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
