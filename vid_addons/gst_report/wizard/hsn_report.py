from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)

class HsnReport(models.TransientModel):

    _name = "gstr.hsn_report"
    
    from_date = fields.Date("From date")
    to_date = fields.Date("To Date")
    company = fields.Many2one("res.company", string="Company", default=lambda self: self.env['res.users']._get_company())
    
    @api.multi
    def print_hsn_report(self):
    	data = {}
    	data["id"] = self.id
    	data["form"] = self.read()[0]
        name = str(self.company.name) +" HSN Report"
    	return{
    		'type':'ir.actions.report.xml',
    		'report_name':'gstr.hsn_report',
    		'datas':data,
            'name':name
    	}