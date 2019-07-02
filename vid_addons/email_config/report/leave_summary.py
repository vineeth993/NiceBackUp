import xlwt
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _
import time
from openerp import api, models, fields, _
import logging 

_logger = logging.getLogger(__name__)

LEAVE_TYPE = {'refuse':'Refused', 'validate1':'Validated', 'validate1':'Validated', 'validate':'Approved', 'confirm':'Sanctioned'}

class leave_summary_report(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(leave_summary_report, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'datetime': dt,
			})
		self.context = context

class LeaveSummary(report_xls):

	def leave_report(self, cr, uid, parser, xls_styles, data, objects, ws, leave_obj):

		name = "Leave Status Report as on "+str(data['form'][0]['to_date'])
		ws.write(0, 0 ,"Nice Chemicals (P) Limited", self.title2)
		ws.write(1, 0 , name, self.title2)


		if data['form'][0]["category"] == "all":
			leave_ids = leave_obj.search(cr, uid, [('state', 'not in', ("cancel", "draft", "refuse")), ("doc_created", ">=", data['form'][0]["from_date"]), ("doc_created", "<=", data['form'][0]['to_date'])], order="id asc")		
		elif data['form'][0]["category"] == "employee":
			leave_ids = leave_obj.search(cr, uid, [('state', 'not in', ("cancel", "draft", "refuse")), ("doc_created", ">=", data['form'][0]["from_date"]), ("doc_created", "<=", data['form'][0]['to_date']), ('employee_id', '=', data['form'][0]['employee_id'][0])], order="id asc")
		elif data['form'][0]["category"] == "department":
			leave_ids = leave_obj.search(cr, uid, [('state', 'not in', ("cancel", "draft", "refuse")), ("doc_created", ">=", data['form'][0]["from_date"]), ("doc_created", "<=", data['form'][0]['to_date']), ('department_id', '=', data['form'][0]['department_id'][0])], order="id asc")
		
		status_obj = self.pool.get("hr.holiday.status")
		leaves = leave_obj.browse(cr, uid, leave_ids)

		leave_status_obj = self.pool.get("hr.holidays.status")
		leave_status = leave_status_obj.browse(cr, uid, data['form'][0]["leave_id"])

		leave_det = []
		for status in leave_status:
			leave_det.append(status.name)

		leave_details = {}
		employer_leave = {}

		for leave in leaves:
			if leave.holiday_status_id.name in leave_det:

				if not employer_leave.has_key(leave.employee_id.name):
					employer_leave.update({leave.employee_id.name:{leave.holiday_status_id.name:0.0}})
				elif not employer_leave[leave.employee_id.name].has_key(leave.holiday_status_id.name):
					employer_leave[leave.employee_id.name].update({leave.holiday_status_id.name:0.0})

				doc_created = dt.strptime(leave.doc_created, '%Y-%m-%d').date().strftime('%d-%m-%Y')

				if leave.date_to:
					date_to = dt.strptime(leave.date_to, '%Y-%m-%d %H:%M:%S').date().strftime('%d-%m-%Y')
				else:
					date_to = ""
				if leave.date_from:
					date_from = dt.strptime(leave.date_from, '%Y-%m-%d %H:%M:%S').date().strftime('%d-%m-%Y')
				else:
					date_from = ""

				val = [leave.employee_id.name, doc_created, leave.name, date_from, date_to]

				if leave.type == "remove":
					val.append("Leave Request")
					val.append(0)
					employer_leave[leave.employee_id.name][leave.holiday_status_id.name] = employer_leave[leave.employee_id.name][leave.holiday_status_id.name] - leave.number_of_days_temp
					val.append(leave.number_of_days_temp)
				elif leave.type == "add":
					val.append("Allocation Request")
					employer_leave[leave.employee_id.name][leave.holiday_status_id.name] = employer_leave[leave.employee_id.name][leave.holiday_status_id.name] + leave.number_of_days_temp
					val.append(leave.number_of_days_temp)
					val.append(0)

				val.append(employer_leave[leave.employee_id.name][leave.holiday_status_id.name])
				val.append(LEAVE_TYPE[leave.state])
				
				if leave_details.has_key(leave.holiday_status_id.name): 
					leave_details[leave.holiday_status_id.name].append(val)
				else:
					leave_details[leave.holiday_status_id.name] = []
					leave_details[leave.holiday_status_id.name].append(val)


		headers = {0:'Employee', 1:'Request/Txn. Type', 2:'Request/Txn. Date', 3:'Description', 4:'Start Date', 5:'End Date', 6:'Leave Addn.', 7:'Leave Dedn.', 8:'Balance', 9:'Status'}
		count = 2

		for header in headers:
			ws.write(count, header, headers[header], self.title2)

		count += 1
		for leaves in leave_details:
			ws.write(count, 0, leaves, self.title2)
			count += 1

			for leave in leave_details[leaves]:

				ws.write(count, 0, leave[0], self.normal)
				ws.write(count, 1, leave[5], self.normal)
				ws.write(count, 2, leave[1], self.normal)
				ws.write(count, 3, leave[2], self.normal)
				ws.write(count, 4, leave[3], self.normal)
				ws.write(count, 5, leave[4], self.normal)
				ws.write(count, 6, leave[6], self.number)
				ws.write(count, 7, leave[7], self.number)
				ws.write(count, 8, leave[8], self.number)
				ws.write(count, 9, leave[9], self.normal)
				count += 1

	def leave_full_report(self, cr, uid, parser, xls_styles, data, objects, ws, leave_obj):

		ws.write(0, 0 ,"Nice Chemicals (P) Limited", self.title2)
		today_date = dt.today().date()
		today_date = today_date.strftime("%d-%m-%Y")
		name = "Leave Status Report as on "+str(today_date)
		ws.write(1, 0 , name, self.title2)

		leave_status_obj = self.pool.get("hr.holidays.status")
		leave_status_id = leave_status_obj.search(cr, uid, [], order="employee_id asc")
		leave_status = leave_status_obj.browse(cr, uid, leave_status_id)

		employee_obj = self.pool.get("hr.employee")
		employee_id = employee_obj.search(cr, uid, [])
		employees = employee_obj.browse(cr, uid, employee_id)

		count = 3
		ws.write(count, 0, "Employee ID", self.title2)
		ws.write(count, 1, "Employee", self.title2)
		ws.write(count, 2, "Employee Company", self.title2)
		ws.write(count, 3, "Employee Department", self.title2)
		column = 3
		for leave in leave_status:
			column += 1
			ws.write(count, column, leave.name, self.title2)

		for employee in employees:
			if employee.employee_id:
				line = 0
				count += 1
				ws.write(count, line, employee.employee_id, self.normal)
				line += 1
				ws.write(count, line, employee.name, self.normal)
				line += 1
				ws.write(count, line, employee.address_id.name, self.normal)
				line += 1
				ws.write(count, line, employee.department_id.name, self.normal)
				for leave in leave_status:
					leave = leave_status_obj.get_days(cr, uid, [leave.id], employee.id)[leave.id]['remaining_leaves']
					line += 1
					ws.write(count, line, leave, self.normal)


	def generate_xls_report(self, parser, xls_styles, data, objects, wb):

		report_name = 'Leave Summary'
		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0
		cols = range(10)

		for col in cols:
			ws.col(col).width = 4000

		cr, uid = self.cr, self.uid

		self.title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz left;')
		self.normal          = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz left;')
		self.number          = xlwt.easyxf(num_format_str='#,##0.00')
		self.number2d        = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		self.number2d_bold   = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on;',num_format_str='#,##0.00;(#,##0.00)')
		leave_obj = self.pool.get("hr.holidays")
		
		if not data['form'][0]["leave_balance"]:
			self.leave_report(cr, uid, parser, xls_styles, data, objects, ws, leave_obj)
		else:
			self.leave_full_report(cr, uid, parser, xls_styles, data, objects, ws, leave_obj)



LeaveSummary('report.leave.summary_report', "leave.report", parser=leave_summary_report)

