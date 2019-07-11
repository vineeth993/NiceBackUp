# -*- coding: utf-8 -*-

import time
from datetime import datetime
import base64
import csv
import StringIO

from openerp import models, api, _, fields

def process_csv_data(csv_data):
    csv_data_lines = base64.decodestring(csv_data).replace("\r","").split("\n")
    datafile = StringIO.StringIO(base64.decodestring(csv_data))
    csvReader = csv.reader(datafile, dialect='excel')
    ret = []
    for line in csvReader:
        cline = []
        for elm in line:
            cline.append(elm.replace('+ACI-','').replace('+AC0-',''))
        ret.append(cline)
    return ret

class partner_import(models.TransientModel):
    _name = 'partner.import'
    _description = 'Partner Import'
    
    partner_file = fields.Binary('CSV File')
    
    @api.one
    def action_import(self):
        data_list = process_csv_data(self.partner_file)
        index = {}
        for x in data_list[0]:
            index[x] = data_list[0].index(x)
        
        partner_obj = self.env['res.partner']
        count = 2
        for data in data_list[1:]:
            code = data[index['PCODE']]
            partner_vals = {
                'ref': code,
                'name': data[index['PNAME']],
                'street': data[index['ADDR1']],
                'street2': data[index['ADDR2']],
                'customer': True,
                'phone': data[index['PHONE']],
                'mobile': data[index['MOBILE']],
                'email': data[index['EMAIL']],
                }
            partner_ids = partner_obj.search([('ref', '=', code)])
            if partner_ids:
                partner = partner_ids[0]
                partner.write(partner_vals)
            else:
                partner = partner_obj.create(partner_vals)
            print 'Updating Line %s/%s'%(count,len(data_list))
            count += 1
        return {'type': 'ir.actions.act_window_close'}