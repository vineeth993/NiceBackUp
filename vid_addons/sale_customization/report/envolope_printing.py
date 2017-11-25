from openerp import api, models
import logging

_logger = logging.getLogger(__name__)

class EnvolopePrinting(models.AbstractModel):

	_name = "report.lr_doc.print_on_envolope"

	@api.model
	def render_html(self, docids, data):
		doc_id = self.env["res.partner"].browse(docids)

		_logger.info("Printing on envolope = "+str(doc_id))
		
		docargs = {
			"doc_ids":docids,
			"docs":doc_id,
			"data" : {}
		}
		return self.env['report'].render("sale_customization.print_on_envolope", docargs)