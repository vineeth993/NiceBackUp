# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Barcode Scanning in Sales & Purchase',
    'version': '1.1',
    'author': 'Cybrosys Technologies',
    'category': 'Product',
    'description': """
                The module allows user to Select Products using a barcode scanner also to autogenerate a barcode for a product .
    """,
    'website': 'www.cybrosys.com',
    'depends': ['sale', 'purchase', 'account', 'product', 'report_xls'],
    'data': [
        'views/sale_purchase_view.xml',
        'views/invoices_view.xml',
        'views/product_view.xml',
        'views/warehouse_button.xml'
    ],

    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
