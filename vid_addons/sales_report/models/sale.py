# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import time

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def print_status_report(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        datas = {
            'ids': ids,
            'form': self.read(cr, uid, ids)[0],
            'object': ids
            }
            
        return { 
            'type': 'ir.actions.report.xml',
            'report_name': 'sale.status.report',
            'datas': datas,
            }

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: