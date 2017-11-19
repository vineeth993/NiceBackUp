from openerp import models, fields, api, _
from openerp.osv import osv
from datetime import date


class CrmStage(models.Model):
    _inherit = 'crm.case.stage'

    calculate_probability = fields.Selection(string="Calculate probability method",
                                             selection=[('stage', 'Stage'), ('manual', 'Manual'),
                                                        ('expected_sell', 'Expected Sell'),
                                                        ], required=True,
                                             default="expected_sell", )

    on_change = fields.Boolean(string='Change Probability Automatically', compute='onchange_calculate_probability',
                               help="Setting this stage will change the probability automatically on the opportunity.",
                               default=False)

    @api.depends('calculate_probability')
    @api.model
    def onchange_calculate_probability(self):
        if self.calculate_probability == 'stage':
            self.on_change = True
        else:
            self.on_change = False


class CrmProducts(models.Model):
    _name = 'crm.products'
    _description = 'CRM Products'

    product_id = fields.Many2one("product.product", "Product", required=True)
    purpose = fields.Many2many('sale.reason', string="Purpose", related='product_id.profiling_seasons')
    crm_lead_id = fields.Many2one("crm.lead", "Lead / Opportunity")
    quantity = fields.Float(string="Quantity", required=True, default=0)
    product_price = fields.Float("Sales Price")
    product_cost_price = fields.Float("Cost Price")
    total_product_cost_price = fields.Float("Total Cost Price")
    total_price = fields.Float(string="Total price", compute="update_total_price", store=True)
    margin = fields.Float(string="Margin", required=False, )
    expected_sell = fields.Integer(string="Expected Sell (%)", required=True, default=0)

    @api.multi
    @api.onchange('product_id')
    def update_price_name(self):
        for record in self:
            record.product_price = record.product_id.lst_price
            record.product_cost_price = record.product_id.standard_price

    @api.depends('quantity', 'product_price')
    @api.multi
    def update_total_price(self):
        for record in self:
            record.total_price = record.product_price * record.quantity
            record.total_product_cost_price = record.product_cost_price * record.quantity
            record.margin = record.total_price - record.total_product_cost_price


class LeadCustom(models.Model):
    _inherit = 'crm.lead'

    lead_type = fields.Selection([(1, 'Direct Lead / Customer'), (2, 'In-Direct Lead /Customer'),
                                  (3, 'Direct Tender'), (4, 'Indirect Tender')], string="Lead Type", required=True, default=1)
    customer_type = fields.Many2one('customer.type', related='partner_id.customer_type', string="Customer Type")
    tender_advertizment_date = fields.Date("Tender Advertizment Date")
    tender_last_date = fields.Date("Tender Last Date")
    tender_opening_date = fields.Date("Tender Opening Date")
    enq_date = fields.Date("Enquiry Date", default=date.today().strftime('%Y-%m-%d'))
    enq_end_date = fields.Date("Enquiry End Date")
    contact_date = fields.Date("Contact Before Date")
    product_ids = fields.One2many("crm.products", "crm_lead_id", "Product")
    planned_revenue = fields.Float(string="Expected Revenue", compute='calculate_revenue', store=True)
    planned_cost = fields.Float(string="Planned Costs", compute='calculate_costs', store=True)
    margin = fields.Float(string="Margin", required=False, compute='calculate_margin', store=True)

    @api.depends('product_ids.total_price')
    @api.multi
    def calculate_revenue(self):
        for order in self:
            for record in order.product_ids:
                order.planned_revenue += record.total_price

    @api.depends('product_ids.total_product_cost_price')
    @api.multi
    def calculate_costs(self):
        for order in self:
            for record in order.product_ids:
                order.planned_cost += record.total_product_cost_price

    @api.depends('product_ids.margin')
    @api.multi
    def calculate_margin(self):
        for order in self:
            for record in order.product_ids:
                order.margin += record.margin

    # @api.onchange('product_ids', 'stage_id')
    @api.onchange('product_ids', 'stage_id')
    @api.multi
    def onchange_product_ids(self):
        for reccord in self:
            total_expected_sell = sum([p.expected_sell for p in reccord.product_ids])
            if self.stage_id:
                if self.stage_id.calculate_probability == 'expected_sell':
                    self.probability = total_expected_sell
                if self.stage_id.calculate_probability == 'stage':
                    self.probability = self.stage_id.probability
            else:
                pass









