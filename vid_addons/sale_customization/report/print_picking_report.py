from openerp import fields, api, models, _
import logging

_logger = logging.getLogger(__name__)

class PrintPicking(models.AbstractModel):

	_name = "report.sale_customization.sale_report_picking"

	@api.model
	def render_html(self, docids, data):

		orders = self.env['sale.order'].browse(docids)
		doc_id = []
		for order in orders:
			stock_search = self.env['stock.picking'].search([('origin', '=', order.name), ('state', 'not in', ('cancel', 'done'))])
			if stock_search:
				doc_id.append(stock_search)

		docargs = {
			"doc_ids":docids,
			"docs":doc_id,
			"data" : {}
			}
		return self.env['report'].render('sale_customization.sale_report_picking', docargs)