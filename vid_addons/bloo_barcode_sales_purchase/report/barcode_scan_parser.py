# -*- coding: utf-8 -*-
from openerp.report import report_sxw

print "ppppppppp"
class barcode_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(barcode_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr': cr,
            'uid': uid,
            'report_name': "Barcode Report",
            'get_month': self._get_month,
        })

    def _get_month(self, data):
        month_lst = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                     'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        return month_lst

