from openerp import api, models, fields


class Invoice(models.Model):
    _inherit = "account.invoice.line"

    barcode_scan = fields.Char(string='Product Barcode', help="Here you can provide the barcode for the product")
    sale_person = fields.Many2one('res.users', string="Sales Person")
    customer = fields.Many2one('res.partner', string="Customer")


