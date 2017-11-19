# -*- encoding: utf-8 -*-
from openerp import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_data = fields.Datetime(comodel_name='sale.order', string='Sale Date',
                                related='order_id.date_order', store=True)


class SaleOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    purchase_data = fields.Datetime(comodel_name='purchase.order', string='Purchase Date',
                                related='order_id.date_order', store=True)


class StockLocation(models.Model):
    _inherit = "stock.location"
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    def compute_location_ids(self):
        location_obj = self.pool.get('stock.location')
        for selff in self:
            res_location_ids = []
            all_loc = location_obj.search(selff._cr, selff._uid, [('usage', '=', 'internal')])
            for j in all_loc:
                complete_name = selff.pool.get('stock.location').browse(selff._cr, selff._uid, j).complete_name
                # print "jesssssssssssssssss", complete_name, selff.view_location_id
                # print "nikkkkkkkkkkkkkkk", complete_name.find(selff.view_location_id.name)
                if selff.view_location_id:
                    if complete_name.find(selff.view_location_id.name) != -1:
                        res_location_ids.append(j)
            selff.location_ids = res_location_ids
    location_ids = fields.One2many('stock.location', 'warehouse_id', compute='compute_location_ids', string='Locations')


class ProductWarehouse(models.Model):
    _name = 'product.warehouse'

    @api.one
    def get_stock_qty(self):
        total_qty_product = 0
        if self.product_id.id:
            self._cr.execute("SELECT  h.product_id,sum(h.qty) as quantity "
                             "FROM stock_quant h "
                             "WHERE h.location_id=%s and h.product_id=%s"
                             " group by h.product_id", (self.location_id.id, self.product_id.id))
            lines_rec = self._cr.dictfetchall()
            if lines_rec:
                total_qty_product = lines_rec[0]['quantity']

        self.stock_qty = total_qty_product

    product_id = fields.Many2one('product.product', string='Product')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    stock_qty = fields.Integer('Qty', compute='get_stock_qty')
    location_id = fields.Many2one('stock.location', string='Location')


class ProductTemplate(models.Model):
    _inherit = "product.product"
    order_partner_id = fields.Many2one('res.partner', string="Partner")

    @api.multi
    def action_sale_product_prices(self):
        id2 = self.env.ref(
            'sale_previous_product_cost.last_sale_product_prices_view')
        sale_lines = self.env['sale.order.line'].search([('product_id', '=', self.id),
                                  ('order_partner_id', '=', self.order_partner_id.id)],
                                 order='create_date DESC')
        return {
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'sale.order.line',
            'views': [(id2.id, 'tree')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('id','in',[" + ','.join(map(str, sale_lines.ids)) + "])]",
        }

    @api.multi
    def action_purchase_product_prices(self):
        id2 = self.env.ref(
            'sale_previous_product_cost.last_sale_product_purchase_prices_view')
        purchase_lines = self.env['purchase.order.line'].search([('product_id', '=', self.id),
                                                         ('partner_id', '=', self.order_partner_id.id)],
                                                        order='create_date DESC')
        return {
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'purchase.order.line',
            'views': [(id2.id, 'tree')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('id','in',[" + ','.join(map(str, purchase_lines.ids)) + "])]",
        }

    @api.one
    def _compute_product_warehouse_ids(self):
        print self
        for wh in self.env['stock.warehouse'].search([]):
            product_wh_exists = self.env['product.warehouse'].search([('product_id', '=', self.id),
                                                                      ('warehouse_id', '=', wh.id)])
            if not product_wh_exists:
                for wh_loc in wh.location_ids:
                    self.env['product.warehouse'].create({'product_id': self.id,
                                                          'warehouse_id': wh.id,
                                                          'location_id': wh_loc.id})
        related_ids = self.env['product.warehouse'].search([('product_id', '=', self.id),
                                                            ('warehouse_id', '!=', None)])
        self.product_warehouse_ids = related_ids

    product_warehouse_ids = fields.One2many('product.warehouse', 'product_id', 'Locations', compute="_compute_product_warehouse_ids")


