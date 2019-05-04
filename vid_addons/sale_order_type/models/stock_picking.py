# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, models, fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        if picking and picking.sale_id:
            sale = picking.sale_id
            if (vals.get('type', '') == 'out_invoice' and
                    sale.type_id.journal_id):
                vals['journal_id'] = sale.type_id.journal_id.id
            elif (vals.get('type', '') == 'out_refund' and
                    sale.type_id.refund_journal_id):
                vals['journal_id'] = sale.type_id.refund_journal_id.id
            if sale.type_id:
                vals['sale_type_id'] = sale.type_id.id
            if sale.sub_type_id:
                vals['sale_sub_type_id'] = sale.sub_type_id.id
        return super(StockPicking, self)._create_invoice_from_picking(picking, vals)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    store_type = fields.Selection([('row_material', 'Raw Material'), ('finish_goods', 'Finished Goods')], string="Picking Type")