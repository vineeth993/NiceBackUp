from openerp import api, models, fields, _
from openerp.osv import osv
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tax_type = fields.Selection([('1', 'Excise'), ('2', 'Non Excise')], string="Tax Type")

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        ir_values = self.pool.get('ir.values')
        if order.tax_type:
            if order.tax_type == '1':
                journal_id = ir_values.get_default(cr, uid, 'sale.config.settings', 'excise_invoice_journal_type')
            elif order.tax_type == '2':
                journal_id = ir_values.get_default(cr, uid, 'sale.config.settings', 'non_excise_invoice_journal_type')
        else:
            journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']
        if not journal_id:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        print ";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id' : order.section_id.id
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals


class sale_order_line_make_invoice(osv.osv_memory):
    _inherit = "sale.order.line.make.invoice"

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        a = order.partner_id.property_account_receivable.id
        if order.partner_id and order.partner_id.property_payment_term.id:
            pay_term = order.partner_id.property_payment_term.id
        else:
            pay_term = False
        ir_values = self.pool.get('ir.values')
        if order.tax_type:
            if order.tax_type == '1':
                journal_id = ir_values.get_default(cr, uid, 'sale.config.settings', 'excise_invoice_journal_type')
            elif order.tax_type == '2':
                journal_id = ir_values.get_default(cr, uid, 'sale.config.settings', 'non_excise_invoice_journal_type')
        else:
            journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']
        if not journal_id:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        return {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': "P%dSO%d" % (order.partner_id.id, order.id),
            'account_id': a,
            'journal_id': journal_id,
            'partner_id': order.partner_invoice_id.id,
            'invoice_line': [(6, 0, lines)],
            'currency_id' : order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'user_id': order.user_id and order.user_id.id or False,
            'company_id': order.company_id and order.company_id.id or False,
            'date_invoice': fields.date.today(),
            'section_id': order.section_id.id,
        }


class sale_advance_payment_inv(osv.osv_memory):
    _inherit = 'sale.advance.payment.inv'

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])

        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            val = inv_line_obj.product_id_change(cr, uid, [], wizard.product_id.id,
                                                 False, partner_id=sale.partner_id.id, fposition_id=sale.fiscal_position.id,
                                                 company_id=sale.company_id.id)
            res = val['value']

            # determine and check income account
            if not wizard.product_id.id:
                prop = ir_property_obj.get(cr, uid,
                                           'property_account_income_categ', 'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                                         _('There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise osv.except_osv(_('Configuration Error!'),
                                     _('There is no income account defined for this product: "%s" (id:%d).') % \
                                     (wizard.product_id.name, wizard.product_id.id,))

            # determine invoice amount
            if wizard.amount <= 0.00:
                raise osv.except_osv(_('Incorrect Data'),
                                     _('The value of Advance Amount must be positive.'))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = sale.amount_untaxed * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = self._translate_advance(cr, uid, percentage=True,
                                                          context=dict(context, lang=sale.partner_id.lang)) % (
                                  wizard.amount)
            else:
                inv_amount = wizard.amount
                if not res.get('name'):
                    # TODO: should find a way to call formatLang() from rml_parse
                    symbol = sale.pricelist_id.currency_id.symbol
                    if sale.pricelist_id.currency_id.position == 'after':
                        symbol_order = (inv_amount, symbol)
                    else:
                        symbol_order = (symbol, inv_amount)
                    res['name'] = self._translate_advance(cr, uid,
                                                          context=dict(context, lang=sale.partner_id.lang)) % symbol_order

            # determine taxes
            if res.get('invoice_line_tax_id'):
                res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
            else:
                res['invoice_line_tax_id'] = False
            ir_values = self.pool.get('ir.values')
            if sale.tax_type:
                if sale.tax_type == '1':
                    journal_id = ir_values.get_default(cr, uid, 'sale.config.settings', 'excise_invoice_journal_type')
                elif sale.tax_type == '2':
                    journal_id = ir_values.get_default(cr, uid, 'sale.config.settings',
                                                       'non_excise_invoice_journal_type')
            else:
                journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)[
                    'journal_id']
            if not journal_id:
                raise osv.except_osv(_('Error!'),
                                     _('Please define sales journal for this company: "%s" (id:%d).') % (
                                         sale.company_id.name, sale.company_id.id))
            # create the invoice
            inv_line_values = {
                'name': res.get('name'),
                'origin': sale.name,
                'account_id': res['account_id'],
                'price_unit': inv_amount,
                'quantity': wizard.qtty or 1.0,
                'discount': False,
                'uos_id': res.get('uos_id', False),
                'product_id': wizard.product_id.id,
                'invoice_line_tax_id': res.get('invoice_line_tax_id'),
                'account_analytic_id': sale.project_id.id or False,
            }
            inv_values = {
                'name': sale.client_order_ref or sale.name,
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': sale.partner_id.property_account_receivable.id,
                'journal_id': journal_id,
                'partner_id': sale.partner_invoice_id.id,
                'invoice_line': [(0, 0, inv_line_values)],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': sale.note,
                'payment_term': sale.payment_term.id,
                'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                'section_id': sale.section_id.id,
            }
            result.append((sale.id, inv_values))
        return result




# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#     tax_type = fields.Selection([('1', 'Excise'), ('2', 'Non Excise')], string="Tax Type")




