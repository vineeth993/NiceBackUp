
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class HrHoliday(models.Model):

	_inherit = "hr.holidays"

	doc_created = fields.Date("Doc Created", default=lambda x:date.today())
	approved_date = fields.Date("Approved Date")
	state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'sanctioned'), ('refuse', 'Refused'), ('validate1', 'Validated'), ('validate', 'Approved')],
            'Status', readonly=True, track_visibility='onchange', copy=False,
            help='The status is set to \'To Submit\', when a holiday request is created.\
            \nThe status is \'To Approve\', when holiday request is confirmed by user.\
            \nThe status is \'Refused\', when holiday request is refused by manager.\
            \nThe status is \'Approved\', when holiday request is approved by manager.')

	def holidays_validate(self, cr, uid, ids, context=None):

		res = super(HrHoliday, self).holidays_validate(cr, uid, ids, context=context)
		self.write(cr, uid, ids, {'approved_date':date.today()})
		return res