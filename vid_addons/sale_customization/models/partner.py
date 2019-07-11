from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)

class CustomerType(models.Model):
    _name = 'customer.type'
    _rec_name = 'customer_type'

    customer_type = fields.Char(string='Customer Type')
    
class ResPartner(models.Model):
    
    _inherit = 'res.partner'

    disc = fields.Float(string='Normal Discount %')
    adisc = fields.Float(string='Additional Discount')
    tdisc = fields.Float(string='T Discount %')
    nedisc = fields.Float(string='Non-Excise Discount %')
    customer_type = fields.Many2one('customer.type', string='Customer Type')
    lead_time = fields.Integer("Lead Time")
    tax_id = fields.Many2many("account.tax", "form_wise_tax_in_partner", "partner_id", "taxes_id", "Customer Taxes")
    tax_desc = fields.Text("Tax Description")  
    disc_id = fields.One2many('partner.discount', 'partner_id', string="Reference", copy=True, track_visibility="onchange")
    
    @api.one
    @api.constrains('ref')
    def _check_reference_len(self):
        if self.is_company:
            if self.ref:
                if len(self.ref) != 7 or self.ref.startswith("PA"):
                    raise ValidationError('Please Check Reference Number in Sales & Purchases Tab')
                else:
                    partner = self.search([('ref', '=', self.ref)])

                    if len(partner) > 1:
                        raise ValidationError('Partner Refernce Already in use')
            else:
                raise ValidationError('Please Provide a reference number in Sales & Purchases Tab')




class PartnerDiscount(models.Model):

    _name = "partner.discount"
    _description = "Partner Discount"

    partner_id = fields.Many2one("res.partner", string="Reference")
    category_id = fields.Many2one("product.brand", string="Product Category")
    normal_disc = fields.Float("Normal Discount")
    additional_disc = fields.Float("Additional Discount")
    target_disc = fields.Float("Target Discount")
