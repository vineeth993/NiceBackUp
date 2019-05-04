# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, fields, models
from openerp.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('partner_id')
    def _get_value(self):
        for order in self:
            if order.partner_id:
                if not order.partner_id.sale_type:
                    raise ValidationError(('Please Select Sale order type under Sales & Purchase tab'))
                else:
                    order.type_id = order.partner_id.sale_type.id
                if not order.partner_id.sale_sub_type_id:
                    raise ValidationError(('Please Select Sub type under Sales & Purchase tab'))
                else:
                    order.sub_type_id = order.partner_id.sale_sub_type_id[0].id
                if order.sub_type_id.tax_categ in ('formstate', 'forminter'):
                    if not order.partner_invoice_id.tax_id:
                        raise ValidationError("Tax are not defined in party master under seetings tab")

    type_id = fields.Many2one(
        comodel_name='sale.order.type', string='Type', readonly=True, compute="_get_value", store=True)
    sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type", readonly=True, compute="_get_value", store=True)
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user)

    # @api.onchange('partner_invoice_id')
    # def onchange_partner_invoice_id(self):
    #     if self.partner_id:
    #         if not self.partner_id.sale_type:
    #             raise ValidationError(('Please Select Sale order type under Sales & Purchase tab'))
    #         else:
    #             self.type_id = self.partner_id.sale_type.id
    #         if not self.partner_id.sale_sub_type_id:
    #             raise ValidationError(('Please Select Sub type under Sales & Purchase tab'))
    #         else:
    #             self.sub_type_id = self.partner_id.sale_sub_type_id[0].id
    #         if self.sub_type_id.tax_categ in ('formstate', 'forminter'):
    #             if not self.partner_invoice_id.tax_id:
    #                 raise ValidationError("Tax are not defined in party master under seetings tab")

    @api.one
    @api.onchange('type_id')
    def onchange_type_id(self):
        self.warehouse_id = self.type_id.warehouse_id
        self.picking_policy = self.type_id.picking_policy
        self.order_policy = self.type_id.order_policy
        if self.type_id.payment_term_id:
            self.payment_term = self.type_id.payment_term_id.id
        if self.type_id.pricelist_id:
            self.pricelist_id = self.type_id.pricelist_id.id
            res = self.onchange_pricelist_id(
                self.pricelist_id.id, self.order_line.ids)
            self.update(res.get('value', {}))
        if self.type_id.incoterm_id:
            self.incoterm = self.type_id.incoterm_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/'and vals.get('partner_id'):
            partner_id = self.env['res.partner'].browse(vals['partner_id'])
            type = partner_id.sale_type
            if type.sequence_id:
                sequence_obj = self.env['ir.sequence']
                vals['name'] = sequence_obj.next_by_id(type.sequence_id.id)
        return super(SaleOrder, self).create(vals)

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        vals = super(SaleOrder, self)._prepare_order_line_procurement(
            order, line, group_id=group_id)
        vals['invoice_state'] = order.type_id.invoice_state
        return vals

    @api.model
    def _prepare_invoice(self, order, line_ids):
        res = super(SaleOrder, self)._prepare_invoice(order, line_ids)
        if order.type_id:
            res['sale_type_id'] = order.type_id.id
        if order.type_id.journal_id:
            res['journal_id'] = order.type_id.journal_id.id
        return res


class Purchase(models.Model):
    _inherit = 'purchase.order'

    def _get_order_type(self):
        return self.env['sale.order.type'].search([("object_type", "=", "purchase")])[:1]

    type_id = fields.Many2one(
        comodel_name='sale.order.type', string='Type', default=_get_order_type)
    sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type")
            
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/' and vals.get('type_id'):
            type = self.env['sale.order.type'].browse(vals['type_id'])

            if type.sequence_id:
                sequence_obj = self.env['ir.sequence']
                vals['name'] = sequence_obj.next_by_id(type.sequence_id.id)
        return super(Purchase, self).create(vals)

  

    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        context = dict(context or {})
        
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')

        res = False
        uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        for order in self.browse(cr, uid, ids, context=context):
            context.pop('force_company', None)
            if order.company_id.id != uid_company_id:
                #if the company of the document is different than the current user company, force the company in the context
                #then re-do a browse to read the property fields for the good company.
                context['force_company'] = order.company_id.id
                order = self.browse(cr, uid, order.id, context=context)
            
            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                if po_line.state == 'cancel':
                    continue
                acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)
                po_line.write({'invoice_lines': [(4, inv_line_id)]})

            # get invoice data and create invoice
            inv_data = self._prepare_invoice(cr, uid, order, inv_lines, context=context)
            inv_data.update({
                'sale_type_id': order.type_id.id,
                'sale_sub_type_id': order.sub_type_id.id
            })
            if order.type_id.purchase_journal_id:
                inv_data['journal_id'] = order.type_id.purchase_journal_id.id
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]})
            res = inv_id
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        res = super(PurchaseOrderLine, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned, name=name, price_unit=price_unit, 
            state=state, context=context)
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        if partner_id:
            lang = partner.lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_obj.browse(cr, uid, product_id, context=context_partner)
        tax_ids = []
        gst, igst = False, False
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        sub_type_id = self.pool.get('sale.order.sub.type').browse(cr, uid, context.get('sub_type_id', None))
        company_gst = company.gst_no and company.gst_no[:2] or ''
        partner_gst = partner.gst_no and partner.gst_no[:2] or ''
        if company_gst and partner_gst:
            if company_gst == partner_gst:
                gst = True
            else:
                igst = True
        else:
            gst = True

        if sub_type_id:
            if sub_type_id and sub_type_id.tax_categ == 'gst':
                gst = True
                igst = False
            elif sub_type_id and sub_type_id.tax_categ == 'igst':
                igst = True
                gst = False
            else:
                gst = igst = False

        for tax in product.supplier_taxes_id:
            if tax.company_id.id == company.id:
                if gst:
                    if tax.tax_categ == 'gst':
                        tax_ids.append(tax.id)
                elif igst:
                    if tax.tax_categ == 'igst':
                        tax_ids.append(tax.id)
        res['value']['taxes_id'] = tax_ids
        return res

