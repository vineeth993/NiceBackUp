# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, models, fields
from openerp.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        if picking and picking.sale_id:
            sale = picking.sale_id
            if (vals.get('type', '') == 'out_invoice' and
                    sale.type_id):
                warehouse_journal_id = self.env["warehouse.journal"].search([('type_id', '=', sale.type_id.id), ('warehouse_id', '=', picking.picking_type_id.default_location_src_id.id)])
                if warehouse_journal_id:
                    vals['journal_id'] = warehouse_journal_id.journal_id.id
                else:
                    # raise ValidationError("Please define journal in sale order type %s for this warehosue %s"%(sale.type_id.name, picking.picking_type_id.default_location_src_id.warehouse_id.name))
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
