
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class HrHoliday(models.Model):

	_inherit = "hr.holidays"

	doc_created = fields.Date("Applied Date", default=lambda x:date.today())
	approved_date = fields.Date("Approved Date")
	is_manager = fields.Boolean("Is manager", compute="_get_manager")
	state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'Confirm'), ('refuse', 'Refused'), ('validate1', 'Sanctioned'), ('validate', 'Approved')],
			'Status', readonly=True, track_visibility='onchange', copy=False,
			help='The status is set to \'To Submit\', when a holiday request is created.\
			\nThe status is \'To Approve\', when holiday request is confirmed by user.\
			\nThe status is \'Refused\', when holiday request is refused by manager.\
			\nThe status is \'Approved\', when holiday request is approved by manager.', default="draft")

	def write(self, cr, uid, ids, vals, context=None):
		employee_id = vals.get('employee_id', False)
		self.add_follower(cr, uid, ids, employee_id, context=context)
		return models.Model.write(self, cr, uid, ids, vals, context=context)

	@api.depends()
	def _get_manager(self):
		for sec in self:
			employee = sec.env['hr.employee'].search([('user_id', '=', sec.env.user.id)])
			sec.is_manager = employee.manager

	def holidays_validate(self, cr, uid, ids, context=None):
		res = super(HrHoliday, self).holidays_validate(cr, uid, ids, context=context)
		self.write(cr, uid, ids, {'approved_date':date.today()})
		return res

	@api.onchange("holiday_status_id")
	def onchange_status(self):
		if self.holiday_status_id.description:
			self.name = self.holiday_status_id.description

class hrHolidayStatus(models.Model):

	_inherit = "hr.holidays.status"

	description = fields.Char(string="Description")