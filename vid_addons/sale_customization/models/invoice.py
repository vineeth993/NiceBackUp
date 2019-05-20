# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
import datetime

import logging

_logger = logging.getLogger(__name__)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _order = 'product_name'

    @api.depends('product_id','invoice_id.extra_discount')
    def _get_product_values(self):
        for line in self:
            line.discount = line.invoice_id.normal_disc
            if line.invoice_id.partner_selling_type == 'special' or line.invoice_id.partner_selling_type == 'extra':
                line.extra_discount = line.invoice_id.nonread_extra_disocunt
            else:
                line.extra_discount = line.invoice_id.extra_discount
            if line.invoice_id.partner_selling_type != "special":
                line.discount = line.invoice_id.normal_disc
            else:
                line.discount = line.invoice_id.nonread_normal_disocunt
    @api.one
    @api.depends('price_unit', 'discount', 'additional_discount','invoice_line_tax_id', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        price_normal = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        price_extra = price_normal * (1 - (self.extra_discount or 0.0) / 100.0)
        price = price_extra * (1 - (self.additional_discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        price_subtotal = taxes['total']
        self.price_subtotal = price_subtotal
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)
            
    @api.depends("product_id")
    def _get_name(self):
        for line in self:
            line.product_name = line.product_id.name

    product_name = fields.Char("Product Name", store=True, compute=_get_name)   
    discount = fields.Float('Discount (%)',compute='_get_product_values', digits_compute= dp.get_precision('Discount'), readonly=True,)
    extra_discount = fields.Float('Extra Discount (%)',compute='_get_product_values', digits_compute= dp.get_precision('Discount'), readonly=True)
    additional_discount = fields.Float('Scheme Discount (%)', digits_compute=dp.get_precision('Discount'))
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'), store=True, readonly=True, compute='_compute_price')

    @api.model
    def move_line_get_item(self, line):
        subtotal = line.price_subtotal
        return {
            'type': 'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'price': subtotal,
            'account_id': line.account_id.id,
            'product_id': line.product_id.id,
            'uos_id': line.uos_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'taxes': line.invoice_line_tax_id,
        }
        
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('partner_id', 'brand_id')
    def _get_extra_discount(self):
        for invoice in self:
            if invoice.partner_selling_type in ('normal', 'extra'):
                partner_brand_id = invoice.env['partner.discount'].search([('partner_id', '=', invoice.partner_id.id), ('category_id', '=', invoice.brand_id.id)])
                if partner_brand_id and invoice.partner_selling_type == 'normal':
                    invoice.normal_disc = partner_brand_id.normal_disc
                    invoice.extra_discount = partner_brand_id.additional_disc
                elif partner_brand_id and invoice.partner_selling_type == 'extra':
                    invoice.normal_disc = partner_brand_id.normal_disc
                    invoice.extra_discount = 0.00
                elif not partner_brand_id and invoice.partner_selling_type in ('normal', 'extra'):
                    invoice.normal_disc = invoice.partner_id.disc
                    invoice.extra_discount = invoice.partner_id.adisc
            else:
                invoice.normal_disc = 0.00
                invoice.extra_discount = 0.00


    def name_get(self, cr, uid, ids, context=None):
        get_value = self.read(cr, uid, ids, ['number', 'date_invoice'], context=context)
        res = []
        for record in get_value:
            if record['date_invoice'] and record['number']:
                date = datetime.datetime.strptime(record['date_invoice'], '%Y-%m-%d').strftime('%d/%m/%Y')
                name = record['number'] +'-'+ date
            else:
                name = 'New'
            res.append((record['id'], name))
        return res

    partner_shipping_id = fields.Many2one("res.partner", string="Shipping Address")
    transaction_type = fields.Selection([('local', 'Local'), ('inter_state', 'Interstate')], 'Transaction Type')
    normal_disc = fields.Float("Normal Discount (%)", compute=_get_extra_discount, digits_compute=dp.get_precision('Account'),store=True)
    partner_selling_type = fields.Selection([('normal', 'Normal'), ('special', 'Special'), ('extra', 'Extra')], string='Selling Type', default="normal")
    extra_discount = fields.Float('Additional Discount(%)', compute=_get_extra_discount, digits_compute=dp.get_precision('Account'),store=True)
    nonread_extra_disocunt = fields.Float('Additional Discount(%)',digits_compute=dp.get_precision('Account'),copy=False)
    nonread_normal_disocunt = fields.Float('Normal Discount',digits_compute=dp.get_precision('Account'),copy=False)
    # extra_discount_amount = fields.Float(string='Extra Discount', readonly=True, compute='_compute_amount', track_visibility='always')
    sale_order = fields.Char("Sale Order", readonly=True, store=True)
    brand_id = fields.Many2one("product.brand", string="Product Type", readonly=True, store=True)
    state = fields.Selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('grn','GRN Created'),
            ('cancel','Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
        payment_term=False, partner_bank_id=False,
        company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(type, partner_id, date_invoice=False,
        payment_term=False, partner_bank_id=False,
        company_id=False)
        for invoice in self:
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                if invoice.move_id.picking_id.order_id.partner_selling_type == 'special' or invoice.move_id.picking_id.order_id.partner_selling_type == 'extra':
                    extra_discount = invoice.nonread_extra_discount
                else:
                    extra_discount = invoice.extra_discount
                if invoice.move_id.picking_id.order_id.partner_selling_type != "special":
                    normal_discount = invoice.normal_disc
                else:
                    normal_discount = invoice.nonread_normal_disocunt
                    
                res['value'].update({
                    'normal_disc': partner.disc,
                    'partner_selling_type': invoice.so_id.partner_selling_type,
                    'extra_discount':partner.adisc,
                })
                users = self.env['res.users'].browse(self._uid)
        return res
    
    @api.onchange('partner_selling_type')
    def onchange_partner_selling_type(self):
        for invoice in self:
            if invoice.partner_selling_type == 'normal':
                invoice.update({
                    'normal_disc':invoice.partner_id.disc,
                    'extra_discount':invoice.partner_id.adisc,
                })
            elif invoice.partner_selling_type == 'extra':
                invoice.update({
                    'normal_disc':invoice.partner_id.disc,
                    'nonread_extra_disocunt':invoice.partner_id.adisc,
                    })
            else:
                invoice.update({
                    'nonread_normal_disocunt':0.0,
                    'nonread_extra_disocunt':0.0,
                    })

    @api.multi
    def action_create_grn(self):
        stock_picking_obj = self.env['stock.picking']
        stock_move_obj = self.env['stock.move']
        types = self.env["stock.picking.type"].sudo().search([("code", "=", "incoming"), ('warehouse_id.type', '=', 'finished'),('warehouse_id.company_id', '=', self.partner_id.parent_id.company_id.id)])
        pack_obj = self.env["stock.pack.operation"]
        pack_ids = []

        if types:
            val = {
                    'move_type':'direct',
                    'invoice_state':'none',
                    'picking_type_id':types[0].id,
                    'origin':self.name,
                    'company_id':self.partner_id.parent_id.company_id.id,
                    'origin':self.number
                }
            stock_id = stock_picking_obj.sudo().create(val)
            for value in self.invoice_line:
                val = {
                        'name':value.product_id.name,
                        'product_id':value.product_id.id,
                        'product_uom': value.uos_id.id,
                        'product_uom_qty':value.quantity,
                        'picking_id':stock_id.id,
                        'location_id':types[0].default_location_src_id.id,
                        'location_dest_id':types[0].default_location_dest_id.id,
                        'company_id':self.partner_id.parent_id.company_id.id
                    }

                pack_val = {
                            'picking_id':stock_id.id,
                            'product_uom_id':value.uos_id.id,
                            'product_id':value.product_id.id,
                            'product_qty':value.quantity,
                            'location_dest_id':types[0].default_location_dest_id.id,
                            'location_id':types[0].default_location_src_id.id,
                            'lot_id':value.lot_id.id
                        }

                stock_move_obj.sudo().create(val)
                pack_id = pack_obj.sudo().create(pack_val) 
                stock_id.sudo().write({'pack_operation_ids':[(4, pack_id.id)]})

            stock_id.sudo().action_confirm()
            self.write({'state':'grn'})

class AccountInvoiceTax(models.Model):

    _inherit = 'account.invoice.tax'

    @api.v8
    def compute(self, invoice):
        tax_grouped = {}
        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))
        company_currency = invoice.company_id.currency_id
        for line in invoice.invoice_line:
            price_normal = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price_extra = price_normal * (1 - (line.extra_discount or 0.0) / 100.0)
            price = price_extra * (1 - (line.additional_discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_id.compute_all(price, line.quantity, line.product_id, invoice.partner_id)['taxes']
            for tax in taxes:
                val = {
                    'invoice_id': invoice.id,
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': currency.round(tax['price_unit'] * line['quantity']),
                }
                if invoice.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['ref_base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['ref_tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                # If the taxes generate moves on the same financial account as the invoice line
                # and no default analytic account is defined at the tax level, propagate the
                # analytic account from the invoice line to the tax line. This is necessary
                # in situations were (part of) the taxes cannot be reclaimed,
                # to ensure the tax move is allocated to the proper analytic account.
                if not val.get('account_analytic_id') and line.account_analytic_id and val['account_id'] == line.account_id.id:
                    val['account_analytic_id'] = line.account_analytic_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = currency.round(t['base'])
            t['amount'] = currency.round(t['amount'])
            t['base_amount'] = currency.round(t['base_amount'])
            t['tax_amount'] = currency.round(t['tax_amount'])

        return tax_grouped
