from openerp import models, fields, api, tools, exceptions, _
from openerp.report import report_sxw
from datetime import datetime


class SalaryReportParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(SalaryReportParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr': cr,
            'uid': uid,
            'get_structure_name': self._get_structure_name,
            'get_heading_name': self._get_heading_name,
            'get_payslip_ids': self._get_payslip_ids
        })

    def _get_structure_name(self):
        struct_ids = self.pool.get('hr.payroll.structure').search(self.cr, self.uid, [])
        struct_obj = self.pool.get('hr.payroll.structure').browse(self.cr, self.uid, struct_ids)
        return struct_obj

    def _get_heading_name(self, data, val):
        date = datetime.strptime(data['date_from'], '%Y-%m-%d')
        year = str(date.year)
        month = date.strftime("%B")
        name = val + " Salary Data " + month + "-" + year

        return name

    def _get_payslip_ids(self, data, val):
        payslip_ids = self.pool.get('hr.payslip').search(self.cr, self.uid, ([('date_from', '=', data['date_from']),
                                                                              ('date_to', '=', data['date_to']),
                                                                              ('state', '=', 'done'),
                                                                              ('struct_id', '=', val.id),
                                                                              ]))
        payslip_obj = self.pool.get('hr.payslip').browse(self.cr, self.uid, payslip_ids)
        return payslip_obj
