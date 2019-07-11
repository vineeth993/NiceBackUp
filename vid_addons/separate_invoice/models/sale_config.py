from openerp import api, fields, models, _


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    excise_invoice_journal_type = fields.Many2one('account.journal', string="Excise Journal")
    non_excise_invoice_journal_type = fields.Many2one('account.journal', string="Non Excise Journal")

    @api.multi
    def set_excise_invoice_journal_type(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'excise_invoice_journal_type', self.excise_invoice_journal_type.id)

    @api.multi
    def set_non_excise_invoice_journal_type(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'non_excise_invoice_journal_type', self.non_excise_invoice_journal_type.id)
