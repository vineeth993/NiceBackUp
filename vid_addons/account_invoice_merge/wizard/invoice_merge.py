# -*- coding: utf-8 -*-
# © 2010-2011 Ian Li <ian.li@elico-corp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class InvoiceMerge(models.TransientModel):
    _name = "invoice.merge"
    _description = "Merge Partner Invoice"

    keep_references = fields.Boolean(
        string='Keep references from original invoices', default=True)
    date_invoice = fields.Date('Invoice Date')

    @api.model
    def _dirty_check(self):
        if self.env.context.get('active_model', '') == 'account.invoice':
            ids = self.env.context['active_ids']
            if len(ids) < 2:
                raise UserError(
                    _('Please select multiple invoice to merge in the list '
                      'view.'))
            inv_obj = self.env['account.invoice'].browse(ids)
            invs = inv_obj.read()
            for d in invs:
                if d['state'] != 'draft':
                    raise UserError(
                        _('At least one of the selected invoices is %s!') %
                        d['state'])
                if d['sale_type_id'] != invs[0]['sale_type_id']:
                    raise UserError(
                        _('Not all invoices are for the same Type') )
                if d['sale_sub_type_id'] != invs[0]['sale_sub_type_id']:
                    raise UserError(
                        _('Not all invoices are for the same Sub Type') )
                if d['sale_type_id'] != invs[0]['sale_type_id']:
                    raise UserError(
                        _('Not all invoices are for the same Type') %
                        d['state'])
                if d['account_id'] != invs[0]['account_id']:
                    raise UserError(
                        _('Not all invoices use the same account!'))
                if d['company_id'] != invs[0]['company_id']:
                    raise UserError(
                        _('Not all invoices are at the same company!'))
                if d['partner_id'] != invs[0]['partner_id']:
                    raise UserError(
                        _('Not all invoices are for the same partner!'))
                if d['type'] != invs[0]['type']:
                    raise UserError(
                        _('Not all invoices are of the same type!'))
                if d['currency_id'] != invs[0]['currency_id']:
                    raise UserError(
                        _('Not all invoices are at the same currency!'))
                if d['journal_id'] != invs[0]['journal_id']:
                    raise UserError(
                        _('Not all invoices are at the same journal!'))
                if d['partner_selling_type'] != invs[0]['partner_selling_type']:
                    raise UserError(
                        _('Not all invoices are of same bill type !'))
                if d['normal_disc'] != invs[0]['normal_disc'] or d['extra_discount'] != invs[0]['extra_discount'] or d['nonread_extra_disocunt'] != invs[0]['nonread_extra_disocunt'] or d['nonread_normal_disocunt'] != invs[0]['nonread_normal_disocunt']:
                    raise UserError(
                        _('Discount percentage are not same'))

        return {}

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        """Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        res = super(InvoiceMerge, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=False)
        self._dirty_check()
        return res

    @api.multi
    def merge_invoices(self):
        """To merge similar type of account invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: account invoice action
        """
        inv_obj = self.env['account.invoice']
        aw_obj = self.env['ir.actions.act_window']
        ids = self.env.context.get('active_ids', [])
        invoices = inv_obj.browse(ids)
        invoices_info, invoice_lines_info = invoices.do_merge(
            keep_references=self.keep_references,
            date_invoice=self.date_invoice
        )
        xid = {
            'out_invoice': 'action_invoice_tree1',
            'out_refund': 'action_invoice_tree3',
            'in_invoice': 'action_invoice_tree2',
            'in_refund': 'action_invoice_tree4',
        }[invoices[0].type]
        action = aw_obj.for_xml_id('account', xid)
        action.update({
            'domain': [('id', 'in', ids + invoices_info.keys())],
        })
        return action
