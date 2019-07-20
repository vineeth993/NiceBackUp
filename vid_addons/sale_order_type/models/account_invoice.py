# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import time
from openerp import api, models, fields


class AccountInvoice(models.Model):
	_inherit = 'account.invoice'

	sale_type_id = fields.Many2one(
		comodel_name='sale.order.type', string='Type')
	sale_sub_type_id = fields.Many2one("sale.order.sub.type", string="Sub Type")

	@api.multi
	def _prepare_refund(self, invoice, date=None, period_id=None,
						description=None, journal_id=None):
		values = super(AccountInvoice, self)._prepare_refund(
			invoice, date, period_id, description, journal_id)
		if invoice.type in ['out_invoice', 'out_refund']:
			journal = False
			if self.type_id:
				journal = self.type_id.refund_journal_id
			else:
				pickings = self.env['stock.picking'].search(
					[('name', '=', invoice.origin)])
				if pickings:
					journal = pickings[0].sale_id.type_id.refund_journal_id
			if journal:
				values['journal_id'] = journal.id
		return values

	@api.multi
	def onchange_partner_id(
		self, type, partner_id, date_invoice=False,
		payment_term=False, partner_bank_id=False,
		company_id=False
	):
		res = super(AccountInvoice, self).onchange_partner_id(
			type, partner_id, date_invoice=date_invoice,
			payment_term=payment_term, partner_bank_id=partner_bank_id,
			company_id=company_id)
		if partner_id:
			partner = self.env['res.partner'].browse(partner_id)
			if partner.sale_type:
				res['value'].update({
					'type_id': partner.sale_type.id,
					'sub_type_id': partner.sale_sub_type_id and partner.sale_sub_type_id[0].id,
				})
		return res

	@api.onchange('sale_type_id')
	def onchange_sale_type_id(self):
		if self.type in ['out_invoice', 'out_refund']:
			if self.sale_type_id.payment_term_id:
				self.payment_term = self.sale_type_id.payment_term_id.id
			if self.sale_type_id.journal_id:
				self.journal_id = self.sale_type_id.journal_id.id
		else:
			pass


class AccountInvoiceLine(models.Model):
	_inherit = 'account.invoice.line'

	@api.multi
	def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, company_id=None):
		res = super(AccountInvoiceLine, self).product_id_change(product=product, uom_id=uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, company_id=company_id)
		tax_ids = []
		gst, igst = False, False
		partner_obj = self.env['res.partner']        
		tax_ids = []
		gst, igst = False, False
		company = self.env.user.company_id
		product_obj = self.env['product.product']
		product_obj = product_obj.browse(product)
		partner = partner_obj.browse(partner_id)
		company = self.env.user.company_id
		sub_type_id = self.env['sale.order.sub.type'].browse(self._context.get('sub_type_id', None))
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

		for tax in product_obj.taxes_id:
			if tax.company_id.id == company.id:
				if gst:
					if tax.tax_categ == 'gst':
						tax_ids.append(tax.id)
				elif igst:
					if tax.tax_categ == 'igst':
						tax_ids.append(tax.id)
		res['value']['invoice_line_tax_id'] = tax_ids
		return res


class account_invoice_refund(models.TransientModel):

	"""Refunds invoice"""

	_inherit = "account.invoice.refund"


	def _get_journal(self, cr, uid, context=None):
		obj_journal = self.pool.get('account.journal')
		user_obj = self.pool.get('res.users')
		invoice_obj = self.pool.get('account.invoice')
		if context is None:
			context = {}
		inv_type = context.get('type', 'out_invoice')
		company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
		type = (inv_type == 'out_invoice') and 'sale_refund' or \
			   (inv_type == 'out_refund') and 'sale' or \
			   (inv_type == 'in_invoice') and 'purchase_refund' or \
			   (inv_type == 'in_refund') and 'purchase'
		journal = obj_journal.search(cr, uid, [('type', '=', type), ('company_id','=',company_id)], limit=1, context=context)
		invoice_id = invoice_obj.search(cr, uid, [('id', 'in', context.get('active_ids'))], limit=1)
		invoice_id = invoice_obj.browse(cr, uid, invoice_id)
		if invoice_id:
			if invoice_id.sale_type_id and invoice_id.sale_type_id.refund_journal_id:
				return invoice_id.sale_type_id.refund_journal_id.id
		return journal and journal[0] or False

	def _get_reason(self, cr, uid, context=None):
		active_id = context and context.get('active_id', False)
		if active_id:
			inv = self.pool.get('account.invoice').browse(cr, uid, active_id, context=context)
			return inv.name
		else:
			return ''

	_defaults = {
		'date': lambda *a: time.strftime('%Y-%m-%d'),
		'journal_id': _get_journal,
		'filter_refund': 'refund',
		'description': _get_reason,
	}

	def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
		journal_obj = self.pool.get('account.journal')
		user_obj = self.pool.get('res.users')
		# remove the entry with key 'form_view_ref', otherwise fields_view_get crashes
		context = dict(context or {})
		context.pop('form_view_ref', None)
		res = super(account_invoice_refund,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		type = context.get('type', 'out_invoice')
		company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
		journal_type = (type == 'out_invoice') and 'sale_refund' or \
					   (type == 'out_refund') and 'sale' or \
					   (type == 'in_invoice') and 'purchase_refund' or \
					   (type == 'in_refund') and 'purchase'
		for field in res['fields']:
			if field == 'journal_id':
				journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', journal_type), ('company_id','in',[company_id])], context=context)
				res['fields'][field]['selection'] = journal_select
				res['fields'][field]['domain'] = [('company_id', '=', company_id)]
			if field == 'period':
				res['fields'][field]['domain'] = [('company_id', '=', company_id)]
		return res


class AccountVoucher(models.Model):
	_inherit = "account.voucher"

	def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
		user_obj = self.pool.get('res.users')
		company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
		res = super(AccountVoucher,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		for field in res['fields']:
			if field == 'journal_id':
				res['fields'][field]['domain'] = [('company_id', '=', company_id)]
		return res


class onshipping(models.TransientModel):

	"""Refunds invoice"""

	_inherit = "stock.invoice.onshipping"

	def _get_journal(self, cr, uid, context=None):
		journal_obj = self.pool.get('account.journal')
		journal_type = self._get_journal_type(cr, uid, context=context)
		journals = journal_obj.search(cr, uid, [('type', '=', journal_type)])
		sale_obj = self.pool.get('sale.order')
		stock_obj = self.pool.get('stock.picking')
		stock_id = stock_obj.search(cr, uid, [('id', 'in', context.get('active_ids'))], limit=1)
		stock_id = stock_obj.browse(cr, uid, stock_id)
		
		warehouse_journal_obj = self.pool.get("warehouse.journal")

		if stock_id:
			order_id = sale_obj.search(cr, uid, [('name', '=', stock_id.origin)])
			order_id = sale_obj.browse(cr, uid, order_id)
			if order_id:
				warehouse_journal_id = warehouse_journal_obj.search(cr, uid, [('type_id', '=', order_id.type_id.id), ('warehouse_id', '=', stock_id.picking_type_id.default_location_src_id.id)])
				warehouse_journal_id = warehouse_journal_obj.browse(cr, uid, warehouse_journal_id)
				if warehouse_journal_id:
					return warehouse_journal_id.journal_id.id
				else:
					# raise ValidationError("Please define journal in sale order type %s for this warehouse %s"%(order_id.type_id.name, stock_id.picking_type_id.default_location_src_id))
					return order_id.type_id.journal_id.id
					# if order_id.type_id and order_id.type_id.journal_id:
					# 	

		return journals and journals[0] or False

	_defaults = {
		'journal_id' : _get_journal,
	}
