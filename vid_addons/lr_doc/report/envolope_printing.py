from openerp import api, models
import logging

_logger = logging.getLogger(__name__)

class EnvolopePrinting(models.AbstractModel):

	_name = "report.lr_doc.print_on_envolope"

	@api.model
	def render_html(self, docids, data):
		_logger.info("context value in render html = "+str(docids))
		if data:
			doc_id = self.env["lr.doc"].browse(data["doc_id"])
		else:
			doc_id = self.env["lr.doc"].browse(docids)

		docargs = {
			"doc_ids":docids,
			"docs":doc_id,
			"data" : {}
		}
		return self.env['report'].render("lr_doc.print_on_envolope", docargs)