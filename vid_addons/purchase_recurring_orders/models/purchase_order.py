# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _prepare_agreement_vals(self, order):
        return {
            'name': order.name,
            'partner_id': order.partner_id.id,
            'company_id': order.company_id.id,
            'start_date': fields.Datetime.now(),
        }

    @api.model
    def _prepare_agreement_line_vals(self, order_line, agreement):
        return {
            'agreement_id': agreement.id,
            'product_id': order_line.product_id.id,
            'discount': order_line.discount,
            'quantity': order_line.product_qty,
        }

    @api.multi
    def action_button_generate_agreement(self):
        agreements = []
        agreement_obj = self.env['purchase.recurring_orders.agreement']
        agreement_line_obj = self.env['purchase.recurring_orders.agreement.line']
        for purchase_order in self:
            agreement_vals = self._prepare_agreement_vals(purchase_order)
            agreement = agreement_obj.create(agreement_vals)
            agreements.append(agreement)
            for order_line in purchase_order.order_line:
                agreement_line_vals = self._prepare_agreement_line_vals(
                    order_line, agreement)
                agreement_line_obj.create(agreement_line_vals)
        if len(agreements) == 1:
            # display the agreement record
            view = self.env.ref(
                'purchase_recurring_orders.'
                'view_purchase_recurring_orders_agreement_form')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.recurring_orders.agreement',
                'res_id': agreement[0].id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'nodestroy': True,
            }
        return True

    from_agreement = fields.Boolean(
        string='From agreement?', copy=False,
        help='This field indicates if the purchase order comes from an agreement.')
    agreement_id = fields.Many2one(
        comodel_name='purchase.recurring_orders.agreement',
        string='Agreement reference', ondelete='restrict')

    @api.multi
    def view_order(self):
        """Method for viewing orders associated to an agreement"""
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': self.env.context,
            'res_id': self[:1].id,
            'view_id': [self.env.ref('purchase.purchase_order_form').id],
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }
