import time
from openerp import fields, models, api
from openerp.osv import osv
from openerp.osv import fields as fld
from openerp.tools.translate import _

TAX_TYPES = [
    ('excise', 'Central Excise'),
    ('cess', 'Cess'),
    ('hedu_cess', 'Higher Education Cess'),
    ('vat', 'VAT'),
    ('add_vat','Additional VAT'),
    ('cst', 'Central Sales Tax'),
    ('service', 'Service Tax'),
    ('tds','Tax Deducted at Source'),
    ('tcs','Tax Collected at Source'),
    ('cform','C Form'),
    ('dform','D Form'),
    ('e1form', 'E1 Form'),
    ('e2form', 'E2 Form'),
    ('fform','F Form'),
    ('hform','H Form'),
    ('iform', 'I Form'),
    ('jform', 'J Form'),
    ('import_duty','Import Duty'),
    ('other', 'Other')
]
class account_tax(models.Model):
    _inherit = 'account.tax'

    tax_categ = fields.Selection(TAX_TYPES, 'Tax Category')
    is_form = fields.Boolean('Form ?')

    def _unit_compute(self, cr, uid, taxes, price_unit, product=None, partner=None, quantity=0):
        taxes = self._applicable(cr, uid, taxes, price_unit , product, partner)
        res = []
        cur_price_unit = price_unit
        for tax in taxes:
            # we compute the amount for the current tax object and append it to the result
            data = {
                'id':tax.id,
                'name':tax.description and tax.description + " - " + tax.name or tax.name,
                'account_collected_id':tax.account_collected_id.id,
                'account_paid_id':tax.account_paid_id.id,
                'account_analytic_collected_id': tax.account_analytic_collected_id.id,
                'account_analytic_paid_id': tax.account_analytic_paid_id.id,
                'base_code_id': tax.base_code_id.id,
                'ref_base_code_id': tax.ref_base_code_id.id,
                'sequence': tax.sequence,
                'base_sign': tax.base_sign,
                'tax_sign': tax.tax_sign,
                'ref_base_sign': tax.ref_base_sign,
                'ref_tax_sign': tax.ref_tax_sign,
                'price_unit': cur_price_unit,
                'tax_code_id': tax.tax_code_id.id,
                'ref_tax_code_id': tax.ref_tax_code_id.id,
                'include_base_amount': tax.include_base_amount,
                'parent_id':tax.parent_id
            }
            res.append(data)
            if tax.type == 'percent':
                amount = cur_price_unit * tax.amount
                data['amount'] = amount

            elif tax.type == 'fixed':
                data['amount'] = tax.amount
                data['tax_amount'] = quantity
                # data['amount'] = quantity
            elif tax.type == 'code':
                localdict = {'price_unit':cur_price_unit, 'product':product, 'partner':partner}
                exec tax.python_compute in localdict
                amount = localdict['result']
                data['amount'] = amount
            elif tax.type == 'balance':
                data['amount'] = cur_price_unit - reduce(lambda x, y: y.get('amount', 0.0) + x, res, 0.0)
                data['balance'] = cur_price_unit

            amount2 = data.get('amount', 0.0)
            if tax.child_ids:
                if tax.child_depend:
                    latest = res.pop()
                amount = amount2
                child_tax = self._unit_compute(cr, uid, tax.child_ids, amount, product, partner, quantity)
                # Add Parent reference in child dictionary of tax so that we can inlcude tha amount of child ...
                for ctax in child_tax:
                    ctax['parent_tax'] = tax.id
                res.extend(child_tax)
                if tax.child_depend:
                    for r in res:
                        for name in ('base', 'ref_base'):
                            if latest[name + '_code_id'] and latest[name + '_sign'] and not r[name + '_code_id']:
                                r[name + '_code_id'] = latest[name + '_code_id']
                                r[name + '_sign'] = latest[name + '_sign']
                                r['price_unit'] = latest['price_unit']
                                latest[name + '_code_id'] = False
                        for name in ('tax', 'ref_tax'):
                            if latest[name + '_code_id'] and latest[name + '_sign'] and not r[name + '_code_id']:
                                r[name + '_code_id'] = latest[name + '_code_id']
                                r[name + '_sign'] = latest[name + '_sign']
                                r['amount'] = data['amount']
                                latest[name + '_code_id'] = False

            if tax.include_base_amount:
                cur_price_unit += amount2
                # Check for Child tax addition. If Tax has childrens and they have also set include in base amount we will add it for next tax calculation...
                for r in res:
                    if 'parent_tax' in r and r['parent_tax'] == tax.id:
                        cur_price_unit += r['amount']
        return res

    @api.onchange('name', 'tax_categ')
    def onchange_tax_type(self):
        result = {}
        vals = []
        for tax in self:
            if tax.tax_categ == 'excise' and tax.name:
                base_code_id = self.env['account.tax.code'].create({'name': 'Edu.cess 2% on '+tax.name})
                vals = [(0,0, {'name':'Edu.cess 2% on '+tax.name,
                     'tax_type':'cess',
                    'sequence':11,
                     'type':'percent',
                     'amount':0.02,
                     'include_base_amount':False,
                     'type_tax_use':'all',
                    'base_code_id':base_code_id,
                    'tax_code_id':base_code_id,
                    }),(0, 0, {'name':'H. Edu.cess 1% on '+tax.name,
                     'tax_type':'hedu_cess',
                    'sequence':12,
                     'type':'percent',
                     'amount':0.01,
                     'include_base_amount':False,
                     'type_tax_use':'all',
                    'base_code_id':base_code_id,
                    'tax_code_id':base_code_id,
                     })]
                base_code_parent_id = self.env['account.tax.code'].create({'name': tax.name})
                result['include_base_amount'] = True
                result['base_code_id'] = base_code_parent_id
                result['tax_code_id'] = base_code_parent_id
            elif tax.tax_categ == 'excise' and not tax.name:
                result['tax_categ'] = False
                result['name'] = 'Excise @ ?? %'
            result['child_ids'] = vals
            return {'value': result}

class account_invoice_tax(models.Model):
    _inherit = 'account.invoice.tax'

    tax_categ = fields.Selection(TAX_TYPES, 'Tax Category')
    form_no = fields.Char('Form No')
    date_iseeu = fields.Date('Issue Date')
    is_form = fields.Boolean('Inter-State Tax')

    @api.multi
    def compute(self, invoice_id):
        res = super(account_invoice_tax, self).compute(invoice_id)

        print "###########################################"
        print res
        for key in res:

            tax_code_id = key[0]
            base_code_id = key[1]
            tax_id = self.env['account.tax'].search([('tax_code_id', '=', tax_code_id), ('base_code_id', '=', base_code_id)])
            for id in tax_id:
                tax = self.env['account.tax'].browse(id.id)
                res[key]['tax_categ'] = tax.tax_categ
                res[key]['is_form'] = tax.is_form
        return res

class res_partner(models.Model):
    _inherit = "res.partner"

    tin_no = fields.Char('TIN Number', size=32, help="Tax Identification Number")
    tin_date = fields.Date('TIN Number Issue Date', help="Tax Identification Number Date of Company")
    cst_no = fields.Char('CST Number', size=32, help='Central Sales Tax Number of Company')
    cst_date = fields.Date('CST Number Issue Date', help='Central Sales Tax Date of Company')
    vat_no = fields.Char('VAT Number', size=32, help="Value Added Tax Number")
    vat_date = fields.Date('VAT Number Issue Date', help='VAT Number Issue Date')
    excise_no = fields.Char('Excise Control Code', size=32, help="Excise Control Code")
    excise_date = fields.Date('Excise Code Issue Date',  help="Excise Code Issue Date")
    service_no = fields.Char('ST Number', size=32, help="Service Tax Number")
    service_date = fields.Date('ST Number Issue Date', help="Issue Date of Service Tax Number")
    pan_no = fields.Char('PAN', size=32, help="Permanent Account Number")
    kgstno = fields.Char(string='KGST No', size=25)
    kgstdt = fields.Date(string='KGST Date')
    salute = fields.Char(string='Salutation', size=5)
    division = fields.Char(string='Excise Division', size=20)

class res_company(models.Model):
    _inherit = 'res.company'

    range = fields.Char('Range', size=64)
    division = fields.Char('Division', size=64)
    commissionerate = fields.Char('Commissionerate', size=64)
    tariff_rate = fields.Integer('Tariff Rate')

    tan_no = fields.Char('Tax Deduction Account Number', size=32, help="Tax Deduction Account Number")

class account_invoice_type(models.Model):

    _name = 'account.invoice.type'
    _description = "Invoice Type"

    name = fields.Char('Name', size=64)
    journal_id = fields.Many2one('account.journal', 'Account Journal')
    type = fields.Selection([
            ('out_invoice', 'Customer Invoice'),
            ('in_invoice', 'Supplier Invoice'),
            ('out_refund', 'Customer Refund'),
            ('in_refund', 'Supplier Refund'),
            ], 'Type', select=True)
    report = fields.Many2one('ir.actions.report.xml', 'Report', domain=[('model', '=', 'account.invoice')])


class product_category(models.Model):
    _inherit = 'product.category'

    hsn = fields.Char('HSN Classification', size=256)
    chapter_no = fields.Char('Ex-Chapeter No.', size=256)
