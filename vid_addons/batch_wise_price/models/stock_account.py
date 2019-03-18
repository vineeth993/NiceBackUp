
from openerp import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):

	_inherit = "stock.picking"

	def _invoice_create_line(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
		invoice_obj = self.pool.get('account.invoice')
		move_obj = self.pool.get('stock.move')
		sale_obj = self.pool.get("sale.order")
		invoices = {}
		is_extra_move, extra_move_tax = move_obj._get_moves_taxes(cr, uid, moves, inv_type, context=context)
		product_price_unit = {}
		for move in moves:
			company = move.company_id
			origin = move.picking_id.name
			sale = move.picking_id.origin
			partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)
			sale_id = sale_obj.search(cr, uid,[('name','=', sale)], context=context)
			key = (partner, currency_id, company.id, user_id)
			invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
			sale_id = sale_obj.browse(cr, uid, sale_id)
			if key not in invoices:
				# Get account and payment terms
				invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
				invoices[key] = invoice_id
			else:
				invoice = invoice_obj.browse(cr, uid, invoices[key], context=context)
				merge_vals = {}
				if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
					invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
					merge_vals['origin'] = ', '.join(invoice_origin)
				if invoice_vals.get('name', False) and (not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
					invoice_name = filter(None, [invoice.name, invoice_vals['name']])
					merge_vals['name'] = ', '.join(invoice_name)
				if merge_vals:
					invoice.write(merge_vals)
			invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=dict(context, fp_id=invoice_vals.get('fiscal_position', False)))
			invoice_line_vals['invoice_id'] = invoices[key]
			invoice_line_vals['origin'] = origin
			# _logger.info("invoice line vals = "+str(invoice_line))
			if not is_extra_move[move.id]:
				product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
			if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
				invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
			if is_extra_move[move.id]:
				desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
					(inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
				invoice_line_vals['name'] += ' ' + desc if desc else ''
				if extra_move_tax[move.picking_id, move.product_id]:
					invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
				#the default product taxes
				elif (0, move.product_id) in extra_move_tax:
					invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]
			if move.lot_ids:
				for quant in move.quant_ids:
					if quant.qty > 0:
						if quant.lot_id.pricelist and not sale_id.partner_selling_type == 'special':
							price_list_obj = self.pool.get('product.price')
							price_list = price_list_obj.search(cr, uid,[('pricelist', '=', quant.lot_id.pricelist.id), ('product_id', '=', invoice_line_vals['product_id'])], context=context)
							if price_list:
								price_list = price_list_obj.browse(cr, uid, price_list, context=context)
								if price_list.cost:
									invoice_line_vals.update({'price_unit':price_list.cost})
						invoice_line_vals.update({'lot_id':quant.lot_id.id,'quantity':quant.qty})
						val = move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
			else:
				move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
			move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)
		invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
		return invoices.values()