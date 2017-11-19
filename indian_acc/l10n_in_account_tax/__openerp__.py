{
    'name': 'Indian Tax Category',
    'version': '1.0',
    'category': 'Indian Localization',
    'description': """Configure Indian Tax with Category
============================================================================================================
- Added tax category on tax to determine different types of taxes during computation and calculations
- Fix a problem of computation of tax (with child tax) on tax, i.e VAT 5% on (product cost + Excise 12.36 %)
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': ['account', 'l10n_in_base'],
    'data': [
        'l10n_in_account_tax_view.xml',
        'report/l10n_in_account_tax_register_view.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
