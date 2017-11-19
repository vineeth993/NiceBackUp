# -*- coding: utf-8 -*-
#
#
#    Author: Romain Deheele
#    Copyright 2015 Camptocamp SA
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
#

from openerp import models, fields, api


class CrmLeadLost(models.TransientModel):
    _name = 'crm.lost'

    reason_id = fields.Many2many('crm.lead.lost.reason', string='Reasons', domain=[('status', '=', 2)])

    @api.one
    def confirm_lost(self):
        leads_id = []
        for i in self.reason_id:
            leads_id.append(i.id)
        obj_lead = self.env['crm.lead'].browse(self._context.get('active_ids'))
        obj_lead.write({'lost_reason_id': [(6, 0, leads_id)]})
        if obj_lead.type == 'lead':
            obj_lead.write({'stage_id': 2})
        if obj_lead.type == 'opportunity':
            obj_lead.write({'stage_id': 7})


class CrmLeadWon(models.TransientModel):
    _name = 'crm.won'

    reason_id = fields.Many2many('crm.lead.lost.reason', string='Reasons', domain=[('status', '=', 1)])

    @api.one
    def confirm_lost1(self):
        leads_id = []
        for i in self.reason_id:
            leads_id.append(i.id)
        obj_lead = self.env['crm.lead'].browse(self._context.get('active_ids'))
        obj_lead.write({'won_reason_id': [(6, 0, leads_id)]})
        if obj_lead.type == 'lead':
            obj_lead.write({'stage_id': 8})
        if obj_lead.type == 'opportunity':
            obj_lead.write({'stage_id': 6})
