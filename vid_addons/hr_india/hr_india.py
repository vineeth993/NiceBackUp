from openerp import models, fields, api
from openerp.exceptions import ValidationError

class hr_employee(models.Model):

    _inherit = 'hr.employee'
         
    date_of_joining = fields.Date(string='Date Of Joining',required=True)
    date_of_conformation = fields.Date(string='Date Of Conformation')
    date_of_resignation = fields.Date(string='Date Of Resignation')
    date_of_relieving = fields.Date(string='Date Of Relieving')

    pancard_card_no = fields.Char(string="PAN Card No")
    aadhar_card_id = fields.Char(string="Aadhar Card Id")
    election_card_id = fields.Char(string="Election Card Id")
    driving_license_no = fields.Char(string="Driving License No")
    provident_fund_no = fields.Char(string="Provident Fund No")

    address_permanent_same_as_address_home = fields.Boolean(string="Same As Home Address")
    address_permanent_id = fields.Many2one(comodel_name='res.partner',string="Permanent Address")

    @api.onchange('address_permanent_same_as_address_home')
    def address_permanent_same_as_address_home_change(self):
        if self.address_permanent_same_as_address_home:
            self.address_permanent_id = self.address_home_id
        else:
            self.address_permanent_id = False


class res_users(models.Model):
    
    _inherit = 'res.users'

    @api.one
    @api.constrains('employee_ids')
    def _check_employee_ids(self):
        if len(self.employee_ids) > 1:
            raise ValidationError("One User (%s) Can Not Be Assigned To Multiple Employees . " % self.name)