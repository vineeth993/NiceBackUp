# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, fields, models



TAX_TYPES = [
    ('gst', 'Local GST'),
    ('igst', 'Interstate GST'),
    ('none', 'None'),
    ]
GST_TYPES = [
    ('cgst', 'CGST'),
    ('sgst', 'SGST'),
    ('igst', 'IGST')]


class SaleOrderTypology(models.Model):
    _name = 'sale.order.type'
    _description = 'Type of sale order'
    _order = 'sequence'

    @api.model
    def _get_domain_sequence_id(self):
        seq_type = self.env.ref('sale.seq_type_sale_order')
        domain = [('code', '=', seq_type.code)]
        return domain

    @api.model
    def _get_selection_picking_policy(self):
        return self.env['sale.order'].fields_get(
            allfields=['picking_policy'])['picking_policy']['selection']

    def default_picking_policy(self):
        default_dict = self.env['sale.order'].default_get(['picking_policy'])
        return default_dict.get('picking_policy')

    @api.model
    def _get_selection_order_policy(self):
        return self.env['sale.order'].fields_get(
            allfields=['order_policy'])['order_policy']['selection']

    def default_order_policy(self):
        default_dict = self.env['sale.order'].default_get(['order_policy'])
        return default_dict.get('order_policy')

    @api.model
    def _get_selection_invoice_state(self):
        return self.env['stock.picking'].fields_get(
            allfields=['invoice_state'])['invoice_state']['selection']

    def default_invoice_state(self):
        default_dict = self.env['stock.picking'].default_get(['invoice_state'])
        return default_dict.get('invoice_state')

    active = fields.Boolean("Active", default=True)
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Entry Sequence', copy=False,)
    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Billing Journal',
        domain=[('type', '=', 'sale')])
    refund_journal_id = fields.Many2one(
        comodel_name='account.journal', string='Refund Billing Journal',
        domain=[('type', '=', 'sale_refund')])
    purchase_journal_id = fields.Many2one(
        comodel_name='account.journal', string='Billing Journal',
        domain=[('type', '=', 'purchase')])
    purchase_refund_journal_id = fields.Many2one(
        comodel_name='account.journal', string='Refund Billing Journal',
        domain=[('type', '=', 'purchase_refund')])
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse', string='Warehouse', required=True)
    picking_policy = fields.Selection(
        selection='_get_selection_picking_policy', string='Shipping Policy',
        required=True, default=default_picking_policy)
    order_policy = fields.Selection(
        selection='_get_selection_order_policy', string='Create Invoice',
        required=True, default=default_order_policy)
    invoice_state = fields.Selection(
        selection='_get_selection_invoice_state', string='Invoice Control',
        required=True, default=default_invoice_state)
    sequence = fields.Integer(
        string='Sequence',
        default=0)
    company_id = fields.Many2one(
        'res.company',
        related='warehouse_id.company_id', store=True, readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterm')
    object_type = fields.Selection([('sale', 'Sale'),
            ('purchase', 'Purchase'),
        ], string="Object Type")

    def onchange_warehouse(self, cr, uid, ids, warehouse_id, context=None):
        if warehouse_id:
            company = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id).company_id
            return {'domain': {
                'journal_id': [('type', '=', 'sale'),('company_id', '=', company.id)],
                'refund_journal_id': [('type', '=', 'sale_refund'), ('company_id', '=', company.id)],
                'purchase_journal_id': [('type', '=', 'purchase'), ('company_id', '=', company.id)],
                'purchase_refund_journal_id': [('type', '=', 'purchase_refund'), ('company_id', '=', company.id)],
            }}
        return {}


class SubType(models.Model):
    _name = 'sale.order.sub.type'
    _description = 'Sub Type of sale order'

    name = fields.Char("Name", required=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id.id)
    type_id = fields.Many2one("sale.order.type", string="Type", required=True)
    # taxes_id = fields.Many2many("account.tax", "sale_order_sub_type_account_tax_rel", "type_id", "tax_id", string="Taxes")
    tax_categ = fields.Selection(TAX_TYPES, 'Tax Category', required=True)
    gst_type = fields.Selection(GST_TYPES, 'GST Type')
    object_type = fields.Selection([
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
        ], string="Object Type", default='sale')