
from openerp import fields, api, models, _
import logging
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class account_invoice_round(models.Model):

	_inherit = "account.invoice"

	round_off_active = fields.Boolean(string="Round Off", compute="get_round_off", store=True)
	round_off_total = fields.Float(string="Rounded Total", compute="_compute_amount", store=True)
	round_off_amount = fields.Float(string="Rounded Amount", compute="_compute_amount", store=True)

	@api.depends("partner_id")
	def get_round_off(self):
		for i in self:
			i.round_off_active = i.company_id.round_off

	@api.one
	@api.depends('invoice_line.price_subtotal', 'tax_line.amount')
	def _compute_amount(self):
		self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
		self.amount_tax = sum(line.amount for line in self.tax_line)
		self.amount_total = self.amount_untaxed + self.amount_tax
		self.round_off_total = round(self.amount_untaxed + self.amount_tax)
		self.round_off_amount = self.round_off_total - self.amount_total

	@api.one
	@api.depends('state', 'currency_id', 'invoice_line.price_subtotal',
		'move_id.line_id.account_id.type',
		'move_id.line_id.amount_residual',
		'move_id.line_id.reconcile_id',
		'move_id.line_id.amount_residual_currency',
		'move_id.line_id.currency_id',
		'move_id.line_id.reconcile_partial_id.line_partial_ids.invoice.type',
		)
	def _compute_residual(self):
		self.residual = 0.0
		partial_reconciliations_done = []
		for line in self.sudo().move_id.line_id:
			if line.account_id.type not in ('receivable', 'payable'):
				continue
			if line.reconcile_partial_id and line.reconcile_partial_id.id in partial_reconciliations_done:
				continue
			if line.currency_id == self.currency_id:
				line_amount = line.amount_residual_currency if line.currency_id else line.amount_residual
			else:
				from_currency = line.company_id.currency_id.with_context(date=line.date)
				line_amount = from_currency.compute(line.amount_residual, self.currency_id)
			if line.reconcile_partial_id:
				partial_reconciliation_invoices = set()
				for pline in line.reconcile_partial_id.line_partial_ids:
					if pline.invoice and self.type == pline.invoice.type:
						partial_reconciliation_invoices.update([pline.invoice.id])
				line_amount = self.currency_id.round(line_amount / len(partial_reconciliation_invoices))
				partial_reconciliations_done.append(line.reconcile_partial_id.id)
			self.residual += line_amount
		self.residual = max(self.residual, 0.0)
		if self.round_off_active and self.type == 'out_invoice':
			self.residual = round(self.residual)




	@api.multi
	def action_move_create(self):
		""" Creates invoice related analytics and financial move lines """
		account_invoice_tax = self.env['account.invoice.tax']
		account_move = self.env['account.move']

		for inv in self:
			if not inv.journal_id.sequence_id:
				raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line:
				raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
			if inv.move_id:
				continue

			ctx = dict(self._context, lang=inv.partner_id.lang)

			company_currency = inv.company_id.currency_id
			if not inv.date_invoice:
				# FORWARD-PORT UP TO SAAS-6
				if inv.currency_id != company_currency and inv.tax_line:
					raise except_orm(
						_('Warning!'),
						_('No invoice date!'
							'\nThe invoice currency is not the same than the company currency.'
							' An invoice date is required to determine the exchange rate to apply. Do not forget to update the taxes!'
						)
					)
				inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
			date_invoice = inv.date_invoice

			# create the analytical lines, one move line per invoice line
			iml = inv._get_analytic_lines()
			# check if taxes are all computed
			compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
			inv.check_tax_lines(compute_taxes)

			# I disabled the check_total feature
			if self.env.user.has_group('account.group_supplier_inv_check_total'):
				if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
					raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

			if inv.payment_term:
				total_fixed = total_percent = 0
				for line in inv.payment_term.line_ids:
					if line.value == 'fixed':
						total_fixed += line.value_amount
					if line.value == 'procent':
						total_percent += line.value_amount
				total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
				if (total_fixed + total_percent) > 100:
					raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

			# Force recomputation of tax_amount, since the rate potentially changed between creation
			# and validation of the invoice
			inv._recompute_tax_amount()
			# one move line per tax line
			iml += account_invoice_tax.move_line_get(inv.id)

			if inv.type in ('in_invoice', 'in_refund'):
				ref = inv.reference
				name = "Inward Supplies"
			else:
				ref = inv.number
				name = "Outward Supplies"

			diff_currency = inv.currency_id != company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)
			
			totlines = []
			ir_config = self.env["ir.values"]
			round_off_acc = inv.company_id.round_off_account
			if inv.payment_term:
				totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
			if totlines:
				res_amount_currency = total_currency
				ctx['date'] = date_invoice
				for i, t in enumerate(totlines):
					if inv.currency_id != company_currency:
						amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
					else:
						amount_currency = False

					# last line: add the diff
					res_amount_currency -= amount_currency or 0
					if i + 1 == len(totlines):
						amount_currency += res_amount_currency
					if self.round_off_active and self.type == "out_invoice":
						if not round_off_acc.id:
							raise ValidationError("Please Define Round off account in company master")
						iml.append({
							'type': 'dest',
							'name': name,
							'price': t[1]+self.round_off_amount,
							'account_id': inv.account_id.id,
							'date_maturity': t[0],
							'amount_currency': diff_currency and amount_currency,
							'currency_id': diff_currency and inv.currency_id.id,
							'ref': ref,
							})
						iml.append({
							'type': 'dest',
							'name': "Round Off",
							'price': -self.round_off_amount,
							'account_id': round_off_acc.id,
							'date_maturity': t[0],
							'amount_currency': diff_currency and amount_currency,
							'currency_id': diff_currency and inv.currency_id.id,
							'ref': ref,
						})
					else:
						iml.append({
							'type': 'dest',
							'name': name,
							'price': t[1],
							'account_id': inv.account_id.id,
							'date_maturity': t[0],
							'amount_currency': diff_currency and amount_currency,
							'currency_id': diff_currency and inv.currency_id.id,
							'ref': ref,
						})
			else:
				if self.round_off_active and self.type == "out_invoice":
					if not round_off_acc.id:
						raise ValidationError("Please Define Round off account in company master")
					iml.append({
						'type': 'dest',
						'name': name,
						'price': total+self.round_off_amount,
						'account_id': inv.account_id.id,
						'date_maturity': inv.date_due,
						'amount_currency': diff_currency and total_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'ref': ref
					})
					iml.append({
						'type': 'dest',
						'name': "Round Off",
						'price': -self.round_off_amount,
						'account_id': round_off_acc.id,
						'date_maturity': inv.date_due,
						'amount_currency': diff_currency and total_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'ref': ref
					})
				else:
					iml.append({
						'type': 'dest',
						'name': name,
						'price': total,
						'account_id': inv.account_id.id,
						'date_maturity': inv.date_due,
						'amount_currency': diff_currency and total_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'ref': ref
					})

			date = date_invoice

			part = self.env['res.partner']._find_accounting_partner(inv.partner_id)

			line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
			line = inv.group_lines(iml, line)

			journal = inv.journal_id.with_context(ctx)
			if journal.centralisation:
				raise except_orm(_('User Error!'),
						_('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

			line = inv.finalize_invoice_move_lines(line)

			move_vals = {
				'ref': inv.reference or inv.name,
				'line_id': line,
				'journal_id': journal.id,
				'date': inv.date_invoice,
				'narration': inv.comment,
				'company_id': inv.company_id.id,
			}
			ctx['company_id'] = inv.company_id.id
			period = inv.period_id
			if not period:
				period = period.with_context(ctx).find(date_invoice)[:1]
			if period:
				move_vals['period_id'] = period.id
				for i in line:
					i[2]['period_id'] = period.id

			ctx['invoice'] = inv
			ctx_nolang = ctx.copy()
			ctx_nolang.pop('lang', None)
			move = account_move.with_context(ctx_nolang).create(move_vals)

			# make the invoice point to that move
			vals = {
				'move_id': move.id,
				'period_id': period.id,
				'move_name': move.name,
			}
			inv.with_context(ctx).write(vals)
			# Pass invoice in context in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			move.post()
		self._log_event()
		return True
