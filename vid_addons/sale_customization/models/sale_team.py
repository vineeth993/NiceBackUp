from openerp import models, api, fields, _


class SalesTeam(models.Model):

	_inherit = 'crm.case.section'

	def name_get(self, cr, uid, ids, context=None):
		"""Overrides orm name_get method"""
		if not isinstance(ids, list):
			ids = [ids]
		res = []
		if not ids:
			return res
		reads = self.read(cr, uid, ids, ['name', 'parent_id'], context)

		for record in reads:
			name = record['name']
			res.append((record['id'], name))
		return res
