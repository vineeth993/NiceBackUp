# -*- coding: utf-8 -*-

import time
from openerp import api, models
import logging

_logger = logging.getLogger(__name__)

class ReportInvoice(models.AbstractModel):
	_name = 'report.nice_gst.report_invoice_gst'

	@api.model
	def render_html(self, docids, data=None):
		if data:
			docs = self.env['account.invoice'].browse(data.get('id', []))
			invoice_id = data['id']
		else:
			docs = self.env['account.invoice'].browse(docids[0])
			invoice_id = docids[0]
		invoice_obj = self.env['account.invoice']
		invoice = invoice_obj.browse(invoice_id)
		templates = {}
		lines = []
		count = 0
		sgst_values = {'2.5': 0.0, '6.0': 0.0, '9.0': 0.0, '14.0': 0.0}
		cgst_values = {'2.5': 0.0, '6.0': 0.0, '9.0': 0.0, '14.0': 0.0}
		igst_values = {'5.0': 0.0, '12.0': 0.0, '18.0': 0.0, '28.0': 0.0}
		taxable_values = {'0.0':0.0, '5.0': 0.0, '12.0': 0.0, '18.0': 0.0, '28.0': 0.0}
		total_nodiscount, total_discount, total_qty = 0.0, 0.0, 0.0
		total_disc_amt = 0
		total_extra_amt = 0
		total_scheme_disc = 0
		disc = 0
		e_disc = 0

		for line in invoice.invoice_line:
			normal_disc = 0
			extra_disc = 0
			add_disc = 0
			count += 1
			total_qty += line.quantity
			subtotal = line.quantity*line.price_unit
			total_nodiscount += subtotal
			discount = subtotal - line.price_subtotal
			discount_perc = round((discount * 100/subtotal), 3)
			total_discount += discount
			taxable_value = line.price_subtotal
			gst_perc, gst, cgst_perc, sgst_perc, igst_perc = 0.0, 0.0, 0.0, 0.0, 0.0
			nogst_amt, sgst_amt, cgst_amt, igst_amt = 0.0, 0.0, 0.0, 0.0
			for tax in line.invoice_line_tax_id:
				gst_perc += tax.amount*100
				if tax.gst_type == 'sgst':
					sgst_perc = tax.amount*100
					sgst_amt  = round(sgst_perc * taxable_value / 100, 2)
				elif tax.gst_type == 'cgst':
					cgst_perc = tax.amount*100
					cgst_amt  = round(cgst_perc * taxable_value / 100, 2)
				elif tax.gst_type == 'igst':
					igst_perc = tax.amount*100
					igst_amt  = round(igst_perc * taxable_value / 100, 2)

			normal_disc = subtotal - ((subtotal * line.discount) / 100)
			extra_disc = normal_disc - ((normal_disc * line.extra_discount) / 100)
			add_disc = extra_disc - ((extra_disc * line.additional_discount) / 100)

			if line.discount:
				total_disc_amt +=  (subtotal - normal_disc)
			if line.extra_discount:
				total_extra_amt += (normal_disc - extra_disc)
			if line.additional_discount:
				total_scheme_disc += (extra_disc - add_disc)

			gst = gst_perc * taxable_value / 100
			gst_perc_str = str(gst_perc)
			sgst_perc_str = str(sgst_perc)
			cgst_perc_str = str(cgst_perc)
			igst_perc_str = str(igst_perc)
			if gst_perc_str in taxable_values:
				taxable_values.update({gst_perc_str: taxable_values[gst_perc_str]+taxable_value})
			if sgst_perc_str in sgst_values:
				sgst_values.update({sgst_perc_str: sgst_values[sgst_perc_str]+sgst_amt})
			if cgst_perc_str in cgst_values:
				cgst_values.update({cgst_perc_str: cgst_values[cgst_perc_str]+cgst_amt})
			if igst_perc_str in igst_values:
				igst_values.update({igst_perc_str: igst_values[igst_perc_str]+igst_amt})
			# if len(line.product_id.name) >= 31:
			#     name = line.product_id.name[0:30]+"\n"+line.product_id.name[30:]
			# else:
			#     name = line.product_id.name
			# _logger.info("Names = "+str(name)+","+str(len(name)))

			batch_no = line.lot_id.name
			disc = line.discount
			e_disc = line.extra_discount
			lines.append({
				's_no': count,
				'hsn': line.product_id.hs_code_id and line.product_id.hs_code_id.code or '',
				'code': line.product_id.default_code,
				'name': line.product_id.name.rsplit("-", 1)[0],
				'b_no':batch_no,
				'volume': line.product_id.volume,
				'volume_uom': line.product_id.product_tmpl_id.uom_id_one.name,
				'weight': line.product_id.weight,
				'weight_uom': line.product_id.product_tmpl_id.uom_id_two.name,
				'weight_net': line.product_id.weight_net,
				'weight_net_uom': line.product_id.product_tmpl_id.uom_id_three.name,
				'qty': line.quantity,
				'price_unit': line.price_unit,
				'disc_perc': discount_perc,
				'discount': '%.2f' % discount,
				'subtotal': '%.2f' % subtotal,
				'gst_perc': gst_perc,
				'gst': '%.2f' % gst,
				'taxable_value': '%.2f' % taxable_value,
				'scheme_disc':line.additional_discount
				})

		sgst_values.update({'sgst_total': sum(sgst_values.values())})
		cgst_values.update({'cgst_total': sum(cgst_values.values())})
		igst_values.update({'igst_total': sum(igst_values.values())})
		total_values = {
			'total_5': (sgst_values['2.5']+cgst_values['2.5']+igst_values['5.0']+taxable_values['5.0']),
			'total_12':(sgst_values['6.0']+cgst_values['6.0']+igst_values['12.0']+taxable_values['12.0']),
			'total_18':(sgst_values['9.0']+cgst_values['9.0']+igst_values['18.0']+taxable_values['18.0']),
			'total_28':(sgst_values['14.0']+cgst_values['14.0']+igst_values['28.0']+taxable_values['28.0']),
			'total_nodiscount': '%.2f' % total_nodiscount,
			'total_discount': '%.2f' % total_discount,
			'total_qty': total_qty
			}
		blank_lines = []
		min_count = 17
		if count < min_count:
			for line_count in range(count+1, min_count):
				blank_lines.append({'no': line_count})
		# elif count > min_count:
		#     for line_count in range(count+1, count+min_count):
		#         blank_lines.append({'no':line_count})
		gst_vals = [sgst_values, cgst_values]
		gst_slabs = ['2.5', '6.0', '9.0', '14.0']        
		for gst_val in gst_vals:
			for gst_slab in gst_slabs:
				gst_val.update({gst_slab: '%.2f' % gst_val[gst_slab]})
		for sgst_val in sgst_values.items():
			if not float(sgst_val[1]):
				sgst_values.update({sgst_val[0]: None})
		for cgst_val in cgst_values.items():
			if not float(cgst_val[1]):
				cgst_values.update({cgst_val[0]: None})
		for igst_val in igst_values.items():
			if not float(igst_val[1]):
				igst_values.update({igst_val[0]: None})
		for taxable_val in taxable_values.items():
			if not float(taxable_val[1]):
				taxable_values.update({taxable_val[0]: None})
		for taxable_val in taxable_values.items():
			if not taxable_val[1]:
				taxable_values.update({taxable_val[0]: None})
		for total_val in total_values.items():
			if not total_val[1]:
				total_values.update({total_val[0]: None})
		docargs = {
			'doc_ids': docids,
			'doc_model': 'account.invoice',
			'data': data,
			'docs': docs,
			'time': time,
			'lines': lines,
			'sgst_values': sgst_values,
			'cgst_values': cgst_values,
			'igst_values': igst_values,
			'taxable_values': taxable_values,
			'total_values': total_values,
			'blank_lines': blank_lines,
			'normal_disc':round(total_disc_amt, 2),
			'add_disc':round(total_extra_amt, 2),
			'scheme_disc':round(total_scheme_disc, 2),
			'disc':disc,
			'e_disc':e_disc
		}
		return self.env['report'].render('nice_gst.report_invoice_gst', docargs)
