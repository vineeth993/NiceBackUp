# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    code = fields.Char(
        string='Lead Number', required=True, default="/", readonly=True)

    _sql_constraints = [
        ('crm_lead_unique_code', 'UNIQUE (code)',
         'The code must be unique!'),
    ]

    @api.model
    def create(self, vals):
        if vals.get('code', '/') == '/':
            if vals.get('lead_type') == 1:
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.lead')
            elif vals.get('lead_type') == 2:
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.lead1')
            elif vals.get('lead_type') == 3:
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.lead2')
            elif vals.get('lead_type') == 4:
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.lead3')
        return super(CrmLead, self).create(vals)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        if self.lead_type == 1:
            default['code'] = self.env['ir.sequence'].get('crm.lead')
        if self.lead_type == 2:
            default['code'] = self.env['ir.sequence'].get('crm.lead1')
        if self.lead_type == 3:
            default['code'] = self.env['ir.sequence'].get('crm.lead2')
        if self.lead_type == 4:
            default['code'] = self.env['ir.sequence'].get('crm.lead3')
        return super(CrmLead, self).copy(default)
