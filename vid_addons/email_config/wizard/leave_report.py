from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class LeaveReport(models.TransientModel):

	_name = "leave.report"

	from_date = fields.Date("From")
	to_date = fields.Date("To")
	category = fields.Selection([('employee', 'Employee'),
								  ('department', 'Department'),
								  ('all', 'All')], string="Category", default="employee")
	employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self:self.env.user.id)
	leave_id = fields.Many2many('hr.holidays.status', "leave_employee_rel", "leave_id", "employee_id", string="Leave")
	description = fields.Boolean('Description')
	department_id = fields.Many2one("hr.department", string="Department")
	leave_balance = fields.Boolean("Leave Balance")

	@api.multi
	def print_leave_report(self):
		
		data = {}
		data["form"] = self.read()

		return {
    		"type":"ir.actions.report.xml",
    		"report_name":"leave.summary_report",
    		"datas":data,
    		"name":"Leave Summary Report"
    	}
