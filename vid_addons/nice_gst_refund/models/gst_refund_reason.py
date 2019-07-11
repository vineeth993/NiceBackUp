# -*- coding: utf-8 -*-


from openerp import api, models, fields


class GstRefundReason(models.Model):
    _name = "gst.refund.reason"

    name = fields.Char(string='Name')
    
    
    
    
