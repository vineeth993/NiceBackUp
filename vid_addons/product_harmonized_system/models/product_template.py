# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2009-2015 Noviat (http://www.noviat.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Luc de Meyer <info@noviat.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp import SUPERUSER_ID

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_default_country(self, cr, uid, *args):
        dataobj7 = self.pool.get('res.country')
        cost_rec7 = dataobj7.search(cr, SUPERUSER_ID, [('code', '=', 'IN')])
        res = dataobj7.browse(cr, SUPERUSER_ID, cost_rec7[0]).id
        return res

    hs_code_id = fields.Many2one(
        'hs.code', string='H.S.Code',
        company_dependent=True, ondelete='restrict',
        help="Harmonised System Code. Nomenclature is "
        "available from the World Customs Organisation, see "
        "http://www.wcoomd.org/. You can leave this field empty "
        "and configure the H.S. code on the product category.")
    origin_country_id = fields.Many2one(
        'res.country', string='Country of Origin',
        help="Country of origin of the product i.e. product "
        "'made in ____'.")

    _defaults = {
        'origin_country_id': _get_default_country,
    }

    @api.multi
    def get_hs_code_recursively(self):
        self.ensure_one()
        if self.hs_code_id:
            res = self.hs_code_id
        elif self.categ_id:
            res = self.categ_id.get_hs_code_recursively()
        else:
            res = None
        return res
