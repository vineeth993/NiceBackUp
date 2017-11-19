from openerp import api, models, fields
from tempfile import TemporaryFile
import base64
import io

class Barcode(models.Model):
    _inherit = 'stock.picking'

    data = fields.Binary("Upload Your Data")
    file_name = fields.Char('File Name')

    @api.multi
    def barcode_upload(self):
        print "fffffffffffffffffffffffff"
        # print self
        dataa = base64.b64decode(self.data)
        xls_filelike = io.BytesIO(dataa)
        workbook = openpyxl.load_workbook(xls_filelike)
        print "ddddddddd",xls_filelike
        split_rec = [xls_filelike.split('\n')][0]
        print split_rec
        for line in split_rec[1::]:
            field_name = [line.split(',')][0]
            print field_name

        fileobj = TemporaryFile('w+')
        fileobj.write(base64.decodestring('data'))
        return

    @api.multi
    def barcode_download(self):
        data = self.read()[0]
        # datas = {
        #     'ids': [],
        #     'model': 'stock.picking',
        #     'form': data
        # }
        return {'type': 'ir.actions.report.xml',
                'report_name': 'barcode.report_xls',
                'datas': data
                }



