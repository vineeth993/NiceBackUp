# -*- coding: utf-8 -*-
from openerp import SUPERUSER_ID
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

    def _get_default_customer(self, cr, uid, context=None):
        user_id = self.pool.get('res.users').browse(cr, uid, uid,context=context)
        return user_id.partner_id.id

    def _get_default_date(self, cr, uid, context=None):
        return time.strftime("%Y-%m-%d")

    def _get_user_details(self, cr, uid, context=None):
        # user_id = self.pool.get('res.users').browse(cr, uid, uid,context=context)
        group_id = self.pool.get('res.groups').search(cr, SUPERUSER_ID, [('name', '=', 'Portal'), ('users', 'in', uid)])
        if group_id:
            return False
        return True

    _columns = {
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
        'prod_or_cust':fields.selection([('prod', 'Product'), ('cust', 'Customer'), ('all', 'All Product'), ('all_order', 'All Order')], string='Product / Customer', default='cust'),
        'customer':fields.many2one("res.partner", string="Customer"),
        'product':fields.many2one("product.product", string="Product"),
        'company_id':fields.many2one("res.company", string="Company"),
        'is_user':fields.boolean(string="Is User")
        }

    _defaults = {
        'date_from': _get_default_date,
        'date_to': _get_default_date,
        'company_id':_get_default_company,
        'customer':_get_default_customer,
        'is_user':_get_user_details
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
