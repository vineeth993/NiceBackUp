
from openerp import fields, api, models, _

import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT

_logger = logging.getLogger(__name__)

class AgeInCompany(models.Model):

	_inherit = 'res.company'

	retirement_age = fields.Integer("Retirement Age", size=2)

class RetirementCalculation(models.Model):

	_inherit = 'hr.employee'

	age = fields.Integer('Age', readonly=True, compute='_compute_retirement_year')
	company_retire_age = fields.Integer('Company Retirement Age', readonly=True,compute='_compute_retirement_year')
	expected_retire_year = fields.Integer('Expected Retirement Year', readonly=True, compute='_compute_retirement_year')
	years_of_service = fields.Integer('Years Of Service', readonly=True, compute='_compute_retirement_year')


	@api.depends('company_id.retirement_age', 'birthday')
	@api.one
	def _compute_retirement_year(self):

		if self.birthday:
			dBday = datetime.strptime(self.birthday, OE_DFORMAT).date()
			dToday = datetime.now().date()
			self.age = dToday.year - dBday.year - ((dToday.month, dToday.day) < (dBday.month, dBday.day))

		if self.birthday and self.company_id.retirement_age:
			expected_retire_year = dBday.year + self.company_id.retirement_age
			self.expected_retire_year = expected_retire_year
			self.years_of_service = expected_retire_year - datetime.now().date().year

		if self.company_id.retirement_age:
			self.company_retire_age = self.company_id.retirement_age
