# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import time

class sale_status_report(osv.osv_memory):
    _name = 'sale.status.report'
    _description = 'Sales Status Report'

    _columns = {
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
        'customer':fields.many2one("res.partner", string="Customer")
        }

    _defaults = {
        'date_from': time.strftime("%Y-01-01"),
        'date_to': time.strftime("%Y-%m-%d")
        }

    def print_sales_report(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        datas = {'ids': ids}
        datas['form'] = self.read(cr, uid, ids)[0]
            
        return { 
            'type': 'ir.actions.report.xml',
            'report_name': 'sale.status.report',
            'datas': datas,
            }

sale_status_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: