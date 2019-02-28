
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class HrHoliday(models.Model):

	_inherit = "hr.holidays"

	doc_created = fields.Date("Doc Created", default=lambda x:date.today())
	approved_date = fields.Date("Approved Date")

	def holidays_validate(self, cr, uid, ids, context=None):

		res = super(HrHoliday, self).holidays_validate(cr, uid, ids, context=context)
		self.write(cr, uid, ids, {'approved_date':date.today()})
		return res