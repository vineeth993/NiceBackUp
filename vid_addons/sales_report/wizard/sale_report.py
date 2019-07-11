# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import time
import logging

_logger = logging.getLogger(__name__)

class sale_status_report(osv.osv_memory):
    _name = 'sale.status.report'
    _description = 'Sales Status Report'

    
    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        return company_id


    _columns = {
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
        'prod_or_cust':fields.selection([('prod', 'Product'), ('cust', 'Customer'), ('all', 'All Product'), ('all_order', 'All Order')], string='Product / Customer', default='cust'),
        'customer':fields.many2one("res.partner", string="Customer"),
        'product':fields.many2one("product.product", string="Product"),
        'company_id':fields.many2one("res.company", string="Company")
        }

    _defaults = {
        'date_from': time.strftime("%Y-01-01"),
        'date_to': time.strftime("%Y-%m-%d"),
        'company_id':_get_default_company
        }

    def print_sales_report(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        datas = {'ids': ids}
        datas['form'] = self.read(cr, uid, ids)[0]
        if datas['form']['prod_or_cust'] == 'cust':
            name = str(datas['form']['customer'][1].split(']')[1]) +"_Pending Report"
        elif datas['form']['prod_or_cust'] == 'prod':
            name = str(datas['form']['product'][1]) +"_Pending Report"
        else:
            name = "Product Pending Report"
          
        return { 
            'type': 'ir.actions.report.xml',
            'report_name': 'sale.status.report',
            'datas': datas,
            'name':name
            }

sale_status_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: