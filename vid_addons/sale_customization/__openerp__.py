# -*- coding: utf-8 -*-

{
    'name': 'Sales Management',
    'version': '1.0',
    'author': 'Steigend IT Solutions',
    'category': 'Sales Management',
    'description': '''
CRM/Sales Customization
  ''',
    'depends': ['base', 'crm', 'report', 'sale', 'sale_stock', 'purchase', 'product', 'stock_account', 'mrp', 'fleet', 'sale_journal', 'stock', 'procurement', 'crm_lead_lost_reason', 'sales_team', 'customer_portal_management'],
    'data': [
        'report.xml',
        'views/lead_view.xml',
        'views/partner_selling_type_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'wizard/warehouse_validation.xml',
        'views/sale_view.xml',
        'views/account_view.xml',
        'views/print_on_envolope.xml',
        'views/sale_report_picking.xml',
        # 'wizard/stock_transfer_details_custom.xml',
        'views/base_view.xml',
        'views/quotation_report.xml',
        'views/reporting.xml',
	'views/stock.xml'
    ],
    'installable': True,
    'auto_install': False

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
