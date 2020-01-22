# -*- coding: utf-8 -*-
# Copyright YEAR(S), AUTHOR(S)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api
from openerp.exceptions import ValidationError
from lxml import etree
import simplejson

import logging

_logger = logging.getLogger(__name__)

class ProductValidator(models.Model):

	_inherit = 'product.template'

	states = fields.Selection([('draft', 'Draft'),
								('confirm', 'Confirm'),
								('validate', 'Validate'),
								('approved','Approved')], string="State", default="draft")
	confirmed_user = fields.Many2one("res.users", string="Confirmed User")

	@api.multi
	def write(self, vals):
		for rec in self:
			if self.states == "approved" and vals.get('qty_available', '/') == '/' and vals.get('incoming_qty', '/') == '/' and vals.get('purchase_incoming_qty', '/') == '/' and vals.get('virtual_available', '/') == '/':
				raise ValidationError("Document is approved cannot be edited please contact administrator")
		return super(ProductValidator, self).write(vals)

	@api.multi
	def reset_to_draft(self):
		self.update({'states':'draft'})

	@api.multi
	def action_confirm(self):
		self.update({'states':'confirm', 'confirmed_user':self.env.user})

	@api.multi
	def action_validate(self):
		# if self.env.user == self.confirmed_user:
		#  	raise ValidationError("User who confirmed doesn't have permission to validate this document")
		self.update({'states':'validate'})

	@api.multi
	def action_approve(self):
		self.update({'states':'approved'})

	@api.multi
	def admin_reset(self):
		self.update({'states':'draft'})