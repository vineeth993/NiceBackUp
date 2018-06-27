from openerp import models, fields, api, _
from openerp.osv import osv
from datetime import date
import datetime
import logging
from openerp import tools
from openerp.tools import email_re, email_split
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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
    _order = 'date_open desc, id desc'

    def get_end_date(self):
        today = date.today()
        end_time = today + datetime.timedelta(days=7)
        return end_time.strftime('%Y-%m-%d')

    sale_id = fields.Many2one('sale.order', string="Sale Order")
    lead_type = fields.Selection([(1, 'Lead Execute Through Company'), (2, 'Lead Execute Through Dealer'),
                                  (3, 'Tender Execute Through Company'), (4, 'Tender Execute Through Dealer')], string="Lead Type", required=True, default=1)
    customer_type = fields.Many2one('customer.type', related='partner_id.customer_type', string="Customer Type")
    tender_advertizment_date = fields.Date("Tender Advertizment Date")
    tender_last_date = fields.Date("Tender Last Date")
    tender_opening_date = fields.Date("Tender Opening Date")
    enq_date = fields.Date("Enquiry Date", default=date.today().strftime('%Y-%m-%d'))
    enq_end_date = fields.Date("Enquiry End Date", default=get_end_date)
    contact_date = fields.Date("Contact Before Date")
    product_ids = fields.One2many("crm.products", "crm_lead_id", "Product")
    planned_revenue = fields.Float(string="Expected Revenue", compute='calculate_revenue', store=True)
    planned_cost = fields.Float(string="Planned Costs", compute='calculate_costs', store=True)
    margin = fields.Float(string="Margin", required=False, compute='calculate_margin', store=True)
    gst_reg = fields.Selection([('registered', 'Registered'), ('unregistered', 'Not Registered')], string="GST Registered", default="unregistered")
    gst_category = fields.Selection([
    ('gst', 'Local'),
    ('igst', 'Interstate'),
    ], string="GST Category")
    gst_no = fields.Char('GST No', size=64)
    ref = fields.Char(string="Reference")
    sale_type = fields.Many2one(
        comodel_name='sale.order.type', string='Sale Order Type',
        company_dependent=True)
    sale_sub_type_id = fields.Many2many("sale.order.sub.type", "sale_order_sub_type_rel", "partner_id", "type_id", string="Sub Type")
    lead_state = fields.Selection([("draft", "Draft"), 
        ("approve", "Waiting For Approval"), 
        ("approved", "Approved"),
        ("quot", "Quotation Created"), 
        ("cancel", "Cancel")], string="State", default='draft')
    city = fields.Many2one("res.city", string="City")
    country_base_gst_type = fields.Selection([('national', 'National'), ('international', 'International')], string="GST Type")

    customer_name = fields.Char(string="Customer Name")
    customer_street1 = fields.Char(string="Address")
    customer_street2  = fields.Char(string="Address2")
    customer_zip = fields.Char(string="PO")
    customer_city = fields.Many2one('res.city', string="City")
    customer_state = fields.Many2one('res.country.state', string="State")
    customer_country = fields.Many2one('res.country', string="Country")
    customer_phone = fields.Char(string="Mobile Number")
    customer_email = fields.Char(string="E-mail")

    def _lead_create_contact(self, cr, uid, lead, name, is_company, parent_id=False, context=None):
        partner = self.pool.get('res.partner')
        vals = {'name': name,
            'user_id': lead.user_id.id,
            'comment': lead.description,
            'section_id': lead.section_id.id or False,
            'parent_id': parent_id,
            'phone': lead.phone,
            'mobile': lead.mobile,
            'email': tools.email_split(lead.email_from) and tools.email_split(lead.email_from)[0] or False,
            'fax': lead.fax,
            'title': lead.title and lead.title.id or False,
            'function': lead.function,
            'street': lead.street,
            'street2': lead.street2,
            'zip': lead.zip,
            'city_id': lead.city.id,
            'country_id': lead.country_id and lead.country_id.id or False,
            'state_id': lead.state_id and lead.state_id.id or False,
            'is_company': is_company,
            'type': 'contact'
        }
        if is_company:
            vals['ref'] = lead.ref
            vals['country_base_gst_type'] = lead.country_base_gst_type
            vals['gst_reg'] = lead.gst_reg
            vals['gst_category'] = lead.gst_category
            vals['gst_no'] = lead.gst_no
            vals['sale_type'] = lead.sale_type.id
            vals['sale_sub_type_id'] = [(6, 0, [sale_sub_type.id for sale_sub_type in lead.sale_sub_type_id])]
        partner = partner.create(cr, uid, vals, context=context)
        return partner

    @api.onchange("customer_city")
    def onchange_customer_city(self):
        if self.customer_city:
            self.customer_state = self.customer_city.state_id

    @api.onchange("customer_state")
    def onchange_customer_state(self):
        if self.customer_state:
            self.customer_country = self.customer_state.country_id

    @api.onchange('city')
    def onchange_city(self):
        if self.city:
            self.state_id = self.city.state_id

    @api.onchange('gst_no', 'country_id')
    def onchange_gst_no(self):
        if self.country_id == self.company_id.country_id:
            self.country_base_gst_type = 'national'
        elif self.country_id:
            self.country_base_gst_type = 'international'

    @api.multi
    def onchange_state(self, state_id):
        res = super(LeadCustom, self).onchange_state(state_id)
        if state_id and state_id == self.env.user.company_id.state_id.id:
            res['value']['gst_category'] = 'gst'
        elif state_id:
            res['value']['gst_category'] = 'igst'
        return res

    @api.multi
    def on_change_partner_id(self, partner_id):
        res = super(LeadCustom, self).on_change_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res['value']['user_id'] = partner.user_id.id or False
            res['value']['city'] = partner.city_id and partner.city_id.id or False
            res['value']['gst_reg'] = partner.gst_reg
            res['value']['gst_no'] = partner.gst_no
            res['value']['ref'] = partner.ref
            res['value']['sale_type'] = partner.sale_type and partner.sale_type.id or False
            res['value']['sale_sub_type_id'] = [(6, 0, [sale_sub_type.id for sale_sub_type in partner.sale_sub_type_id])]
        return res

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

    @api.multi
    def action_approve(self):
        self.lead_state = "approve"

    @api.multi
    def action_approved(self):
        if self.ref:
            partner = self.env['res.partner'].search([('ref', '=', self.ref)])
            if partner:
                raise ValidationError("Partner Reference already exist")
        if not self.partner_name or not self.ref or not self.sale_sub_type_id or not self.sale_type:
            raise ValidationError("Please Enter These Fields Company Name, Reference, Sale Order Type, Sub Type")
        self.lead_state = "approved"

    @api.multi
    def action_reset(self):
        self.write({"stage_id":1})
        self.lead_state = "draft"

    @api.model
    def create(self, vals):
        vals = super(LeadCustom, self).create(vals)
        if vals["partner_id"]:
            vals["lead_state"] = "approved"
        return vals

    # @api.model
    # def write(self, vals):
    #     _logger.info("The value before updation is ="+str(vals))
    #     vals = super(LeadCustom, self).write(vals)
    #     if vals["partner_id"]:
    #         vals["lead_state"] = "approved"
    #     else:
    #         vals["lead_state"] = "approve"
    #     _logger.info("In write Function = "+str(vals))
    #     return vals

    def _create_lead_partner(self, cr, uid, lead, context=None):
        partner_id = False
        contact_id = False
        if lead.partner_name and lead.contact_name:
            partner_id = self._lead_create_contact(cr, uid, lead, lead.partner_name, True, context=context)
            contact_id = self._lead_create_contact(cr, uid, lead, lead.contact_name, False, partner_id, context=context)
        elif lead.partner_name and not lead.contact_name:
            partner_id = self._lead_create_contact(cr, uid, lead, lead.partner_name, True, context=context)
        elif not lead.partner_name and lead.contact_name:
            contact_id = self._lead_create_contact(cr, uid, lead, lead.contact_name, False, context=context)
        elif lead.email_from and self.pool.get('res.partner')._parse_partner_name(lead.email_from, context=context)[0]:
            contact_name = self.pool.get('res.partner')._parse_partner_name(lead.email_from, context=context)[0]
            contact_id = self._lead_create_contact(cr, uid, lead, contact_name, False, context=context)
        else:
            raise osv.except_osv(
                _('Warning!'),
                _('No customer name defined. Please fill one of the following fields: Company Name, Contact Name or Email ("Name <email@address>")')
            )
        return partner_id or contact_id
