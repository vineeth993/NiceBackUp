
from openerp import fields, models, api, exceptions, _
from openerp.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class HrHoliday(models.Model):

	_inherit = "hr.holidays"
	_order = "doc_created asc"

	doc_created = fields.Date("Applied Date", default=lambda x:date.today())
	approved_date = fields.Date("Approved Date")
	is_manager = fields.Boolean("Is manager", compute="_get_manager")
	state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'Confirm'), ('refuse', 'Refused'), ('validate1', 'Sanctioned'), ('validate', 'Approved')],
			'Status', readonly=True, track_visibility='onchange', copy=False,
			help='The status is set to \'To Submit\', when a holiday request is created.\
			\nThe status is \'To Confirm\', when holiday request is confirmed by creater.\
			\nThe status is \'Sanctioned\', when holiday request is sanctiones by the department manager.\
			\nThe status is \'Refused\', when holiday request is refused by manager.\
			\nThe status is \'Approved\', when holiday request is approved by HR Department.', default="draft")

	def create(self, cr, uid, values, context=None):

		hr_holiday_id = super(HrHoliday, self).create(cr, uid, values, context=context)
		period_id = self.pool.get('account.fiscalyear').find(cr, uid, values['date_from'], context=context)
		get_period_id = self.pool.get('account.fiscalyear').browse(cr, uid, period_id, context=context)
		employee_id = self.pool['hr.employee'].browse(cr, uid, values['employee_id'], context=context) 

		holiday_status_id = self.pool['hr.holidays.status'].browse(cr, uid, values['holiday_status_id'], context=context)

		if holiday_status_id.leave_limit:
			get_leaves = self.pool['hr.holidays'].search(cr, uid, [('employee_id', '=', values['employee_id']), ('holiday_status_id', '=', holiday_status_id.id),('date_from', '>=', get_period_id.date_start),('date_from', '<=', get_period_id.date_stop)], context=context)
			if len(get_leaves) >= holiday_status_id.leave_limit:
				raise ValidationError("Your %s Leave limit has reached ,You cannot apply for %s for this financial year" %(holiday_status_id.name, holiday_status_id.name))

		if holiday_status_id.leave_days_limit:
			if values["number_of_days_temp"] > holiday_status_id.leave_days_limit:
				raise ValidationError("You cannot apply for more than %d days for %s "%(holiday_status_id.leave_days_limit, holiday_status_id.name))

		return hr_holiday_id

	def write(self, cr, uid, ids, vals, context=None):
		employee_id = vals.get('employee_id', False)
		self.add_follower(cr, uid, ids, employee_id, context=context)
		return models.Model.write(self, cr, uid, ids, vals, context=context)

	@api.depends()
	def _get_manager(self):
		for sec in self:
			employee = sec.env['hr.employee'].search([('user_id', '=', sec.env.user.id)])
			sec.is_manager = employee.manager

	@api.onchange("holiday_status_id")
	def onchange_status(self):
		if self.holiday_status_id.description:
			self.name = self.holiday_status_id.description

	@api.multi
	def action_cancel(self):
		for obj in self:
			obj.write({'state':'cancel'})
			obj.message_post(_("%s %s has been Cancelled")%(obj.employee_id.name,obj.holiday_status_id.name))
		self.holidays_cancel()

	def holidays_validate(self, cr, uid, ids, context=None):
		obj_emp = self.pool.get('hr.employee')
		ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
		manager = ids2 and ids2[0] or False
		self.write(cr, uid, ids, {'state':'validate'})
		data_holiday = self.browse(cr, uid, ids)
		for record in data_holiday:
			if record.double_validation:
				self.write(cr, uid, [record.id], {'manager_id2': manager})
			else:
				self.write(cr, uid, [record.id], {'manager_id': manager})
			if record.holiday_type == 'employee' and record.type == 'remove':
				meeting_obj = self.pool.get('calendar.event')
				meeting_vals = {
					'name': record.name or _('Leave Request'),
					'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
					'duration': record.number_of_days_temp * 8,
					'description': record.notes,
					'user_id': record.user_id.id,
					'start': record.date_from,
					'stop': record.date_to,
					'allday': False,
					'state': 'open',            # to block that meeting date in the calendar
					'class': 'confidential'
				}   
				#Add the partner_id (if exist) as an attendee             
				if record.user_id and record.user_id.partner_id:
					meeting_vals['partner_ids'] = [(4,record.user_id.partner_id.id)]
					
				ctx_no_email = dict(context or {}, no_email=True)
				meeting_id = meeting_obj.create(cr, uid, meeting_vals, context=ctx_no_email)
				self._create_resource_leave(cr, uid, [record], context=context)
				self.write(cr, uid, ids, {'meeting_id': meeting_id})
			elif record.holiday_type == 'category':
				emp_ids = obj_emp.search(cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
				leave_ids = []
				batch_context = dict(context, mail_notify_force_send=False)
				for emp in obj_emp.browse(cr, uid, emp_ids, context=context):
					vals = {
						'name': record.name,
						'type': record.type,
						'holiday_type': 'employee',
						'holiday_status_id': record.holiday_status_id.id,
						'date_from': record.date_from,
						'date_to': record.date_to,
						'notes': record.notes,
						'number_of_days_temp': record.number_of_days_temp,
						'parent_id': record.id,
						'employee_id': emp.id
					}
					leave_ids.append(self.create(cr, uid, vals, context=batch_context))
				for leave_id in leave_ids:
					# TODO is it necessary to interleave the calls?
					for sig in ('confirm', 'validate', 'second_validate'):
						self.signal_workflow(cr, uid, [leave_id], sig)
			self.message_post(cr, uid, [record.id],_("%s %s has been approved."%(record.employee_id.name,record.holiday_status_id.name)), context=context)
			self.write(cr, uid, ids, {'approved_date':date.today()})
		return True

	def holidays_first_validate_notificate(self, cr, uid, ids, context=None):
		for record in self.browse(cr, uid, ids, context=context):
			self.message_post(cr, uid, [record.id],
				_("%s %s has been Sanctioned, waiting second validation."%(record.employee_id.name,record.holiday_status_id.name)), context=context)

class hrHolidayStatus(models.Model):

	_inherit = "hr.holidays.status"

	description = fields.Char(string="Description")
	leave_limit = fields.Float(string="Leave Limit")
	leave_days_limit = fields.Float(string="Leave Days Limit")