# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, exceptions

class crm_lead2opportunity_partner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    
    @api.multi
    def action_apply(self):
        lead = self.env['crm.lead'].browse(self._context['active_id'])
        for line in lead.product_ids:
            if line.quantity <= 0:
                raise exceptions.Warning('Quantity cannot be less than zero')
        return super(crm_lead2opportunity_partner, self).action_apply()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
