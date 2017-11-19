{
    'name': 'Separate Invoice1',
    'author': 'Nilmar Shereef',
    'depends': ['sale', 'account'],
    'summary': """This module creates separate invoices for service products and Stockable-Consumable products""",
    'author': "Nilmar Shereef",

    'website': "http://www.Cybrosys.com",
    'installable': "True",
    'category': 'Invoicing',
    'version': '0.1',
    'data': [
        'views/sale_config_settings_views.xml',
        'views/sale_order_view.xml',
        ],
    'installable' : True,
}