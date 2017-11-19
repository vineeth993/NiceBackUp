from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class PartnerSellingtype(models.Model):
    _name = 'partner.selling.type'
    
    name = fields.Char('Name')
    partner_type = fields.Selection([('normal','Normal'),('extra','Extra'),('special','Special')],string="Partner selling type")
    disocunt = fields.Float('Discount(%)',digits_compute=dp.get_precision('Account'))
    
    