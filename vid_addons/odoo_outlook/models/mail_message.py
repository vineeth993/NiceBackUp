# -*- coding: utf-8 -*-

from openerp import models, fields, api


class mail_message(models.Model):
    _inherit = 'mail.message'

    from_outlook = fields.Boolean(string='Added from Outlook', default=False)

    @api.cr_uid_context
    def message_read(self, cr, uid, ids=None, domain=None, message_unload_ids=None,
                        thread_level=0, context=None, parent_id=False, limit=None):
        msgs = super(mail_message, self).message_read(cr, uid, ids, domain, message_unload_ids,
                        thread_level, context, parent_id, limit)
        for msg in msgs:
            if msg.get('id'):
                msg['from_outlook'] = self.browse(cr, uid, [msg['id']])[0].from_outlook

        return msgs