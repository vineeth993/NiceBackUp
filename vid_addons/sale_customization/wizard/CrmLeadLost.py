from openerp import models, fields, api

class CrmLeadLost(models.TransientModel):

	_inherit = "crm.lost"

	@api.multi
	def confirm_lost(self):
		super(CrmLeadLost, self).confirm_lost()
		lead_obj = self.env["crm.lead"].browse(self._context.get("active_ids"))
		lead_obj.write({"lead_state":"cancel"})