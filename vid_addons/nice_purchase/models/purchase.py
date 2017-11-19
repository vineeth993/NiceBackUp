# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    def open_form_view(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'nice_purchase', 'view_order_line_form')

        line = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Order Line"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'purchase.order.line',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'res_id': line.id
        }

    def button_save(self, cr, uid, ids, context=None):
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: