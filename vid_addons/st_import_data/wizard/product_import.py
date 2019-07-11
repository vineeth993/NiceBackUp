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

class product_import(models.TransientModel):
    _name = 'product.import'
    _description = 'Products Import'
    
    product_file = fields.Binary('CSV File')
    
    @api.one
    def action_import(self):
        data_list = process_csv_data(self.product_file)
        index = {}
        for x in data_list[0]:
            index[x] = data_list[0].index(x)
        prod_obj = self.env['product.template']
        uom_obj = self.env['product.uom']
        uom_categ_id = self.env['product.uom.categ'].search([('name', '=', 'Unit')]).id
        brand_obj = self.env['product.brand']
        brand_ids = brand_obj.search([('name', '=', 'NICE CHEMICALS')])
        if brand_ids:
            brand_id = brand_ids.id
        else:
            brand_id = brand_obj.create({'name': 'NICE CHEMICALS'}).id
        count = 2
        for data in data_list[1:]:
            code = data[index['ICODE']]
            uom_name = data[index['UOM']]
            weight = data[index['PACK']]
            name = data[index['INAME']] + ' ' + data[index['PACK']] + ' ' + uom_name
            product_vals = {
                #'default_code': code,
                #'name': name,
                #'gcode': data[index['GCODE']],
                #'product_brand_id': brand_id,
                'weight': weight,
                'list_price': data[index['SCOST']],
                'standard_price': data[index['CPRICE']]
                }
            if uom_name:
                uom_ids = uom_obj.search([('name', '=', uom_name)])
                uom_id = uom_ids and uom_ids[0].id or False
                if not uom_id:
                    uom_id = uom_obj.create({
                        'name': data[index['UOM']],
                        'category_id': uom_categ_id
                        }).id
                product_vals.update({'uom_id': uom_id, 'uom_id_two': uom_id})
            product_ids = prod_obj.search([('default_code', '=', code)])
            if product_ids:
                product = product_ids[0]
                product.write(product_vals)
            else:
                product = prod_obj.create(product_vals)
            print 'Updating Line %s/%s'%(count,len(data_list))
            count += 1
        return {'type': 'ir.actions.act_window_close'}
