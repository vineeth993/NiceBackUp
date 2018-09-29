from openerp import fields, models, api, _
import logging
import json
import base64
import datetime
from collections import OrderedDict
import re
import os
import tempfile

_logger = logging.getLogger(__name__)

DISPATCH_MODE = [(1, "Road"),
		(2, "Rail"),
		(3, "Air"),
		(4,"Ship")]

SUPPLY_TYPE = [('I', 'Inward'),
				('O', 'Outward')]

VEHICLE_TYPE = [('R', 'Regular'),
				('O', 'ODC')]

SUB_TYPE = [(1, 'Supply'),
			(2, 'Import'),
			(3, 'Export'),
			(4, 'Job Work'),
			(5, 'For Own Use'),
			(6, 'Job Work Returns'),
			(7, 'Sales Returns'),
			(8, 'Others'),
			(9, 'SKD/CKD'),
			(10, 'Line Sales'),
			(11, 'Recipient Not Known'),
			(12, 'Exibhition or Fairs')]

DOC_TYPE = [('INV', 'Tax Invoice'),
			('BIL', 'Bill Of Supply'),
			('BOE', 'Bill Of Entry'),
			('CHL', 'Delivery Challan'),
			('CNT', 'Credit Note'),
			('OTH', 'Others')]


class GetEwpdc(models.TransientModel):

	_name = "dcewp.json"

	name = fields.Char('Doc Id', readonly=True)
	from_addr = fields.Many2one('res.partner', string="From Partner", readonly=True)
	to_addr = fields.Many2one('res.partner', string="To Partner", readonly=True)
	transport_mode = fields.Selection(DISPATCH_MODE, string="Transport Mode", default=1)
	supply_type = fields.Selection(SUPPLY_TYPE, string="Supply Type", default='O')
	sub_type = fields.Selection(SUB_TYPE, string="Sub Type", default=5)
	vehicle_type = fields.Selection(VEHICLE_TYPE, string="Vehicle Type", default="R")
	doc_type = fields.Selection(DOC_TYPE, string="Doc Type", default="INV")
	transport_distance = fields.Integer('Distance')
	transporter_name = fields.Char('Transporter Name')
	transporter_id = fields.Char('Transporter GST')
	trans_doc_no = fields.Char('Document Number')
	trans_doc_date = fields.Date('Document Date')
	vehicle_number = fields.Char('Vehicle Number')
	to_zip_code = fields.Char("To Zipcode", required=True)

	@api.model
	def default_get(self, fields):

		res = super(GetEwpdc, self).default_get(fields)
		invoices = []
		lr_id = self.env['multi.stock.outward'].browse(self._context.get('active_ids', []))
		if lr_id:
			res['name'] = lr_id.name
			res['from_addr'] = lr_id.company_id.partner_id.id
			res['to_addr'] = lr_id.partner_id.id
			res['to_zip_code'] = lr_id.partner_id.zip
		return res
		
	@api.multi
	def get_json(self):

		billLists = []

		hsn_temp = []
		lr_id = self.env['multi.stock.outward'].browse(self._context.get('active_ids', []))
		item_no = 0
		item_list = OrderedDict()
		inv_total, inv_tax = 0, 0
		for line in lr_id.stock_line_id:
			hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total = 0, 0, 0, 0
			hsn_total_taxablevalue = 0
			
			val = None
			tax_percnt = 0.0
			if line.last_issued_stock:

				hsn_total_taxablevalue += (line.unit_price * line.last_issued_stock)
				inv_total += hsn_total_taxablevalue
				for tax in line.taxes_id:
					if tax.gst_type == "cgst":
						hsn_cgst_total += round((line.unit_price * tax.amount), 2)
					elif tax.gst_type == "sgst":
						tax_percnt = (tax.amount * 2)*100
						val = "State"
						hsn_sgst_total = round((line.unit_price * tax.amount), 2)
					elif tax.gst_type == "igst":
						tax_percnt = (tax.amount)*100
						val = "Inter"
						hsn_igst_total = round((line.unit_price * tax.amount), 2)
					elif tax.gst_type == "cess":
						hsn_cess_total = round((line.unit_price * tax.amount), 2)
				inv_tax += (hsn_cgst_total + hsn_sgst_total + hsn_igst_total + hsn_cess_total)
				if not item_list.has_key(line.product_id.hs_code_id.code[0:2]):
					item_list.update({line.product_id.hs_code_id.code[0:2]:{round(tax_percnt, 2):[round(hsn_total_taxablevalue, 2), round(hsn_igst_total, 2), round(hsn_sgst_total, 2), round(hsn_cgst_total, 2), round(hsn_cess_total, 2), line.last_issued_stock, val, line.product_id.hs_code_id.description]}})
				else:
					if not item_list[line.product_id.hs_code_id.code[0:2]].has_key(round(tax_percnt, 2)):
						item_list[line.product_id.hs_code_id.code[0:2]].update({round(tax_percnt, 2):[round(hsn_total_taxablevalue, 2), round(hsn_igst_total, 2), round(hsn_sgst_total, 2), round(hsn_cgst_total, 2), round(hsn_cess_total, 2), line.last_issued_stock, val, line.product_id.hs_code_id.description]})
					else:
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][0] += round(hsn_total_taxablevalue, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][1] += round(hsn_igst_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][2] += round(hsn_sgst_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][3] += round(hsn_cgst_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][4] += round(hsn_cess_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][5] += line.last_issued_stock

		itemList = []
		billList = {}
		totalCgst, totalSgst, totalIgst, totalCess = 0, 0, 0, 0		
		for hsn in item_list:
			for item in item_list[hsn]:
				# _logger.info("The item list = "+str(item))
				items = {}
				item_no += 1
				items['itemNo'] = item_no
				items['productName'] = item_list[hsn][item][7]
				items['productDesc'] = item_list[hsn][item][7]
				items['hsnCode'] = int(hsn)
				items['quantity'] = item_list[hsn][item][5]
				items['qtyUnit'] = 'NOS'
				items['taxableAmount'] = round(item_list[hsn][item][0], 2)
				if item_list[hsn][item][6] == 'Inter':
					items['sgstRate'] = 0
					items['cgstRate'] = 0
					items['igstRate'] = item
				else:
					items['sgstRate'] = item / 2
					items['cgstRate'] = item / 2
					items['igstRate'] = 0										
				items['cessRate'] = 0
				totalIgst += item_list[hsn][item][1]
				totalSgst += item_list[hsn][item][2]
				totalCgst += item_list[hsn][item][3]
				totalCess += item_list[hsn][item][4]
				itemList.append(items)

		invoice_date = datetime.datetime.strptime(lr_id.quant_issued_date, "%Y-%m-%d").strftime("%d/%m/%Y")
		trans_date = ""
		transporter_id = ""
		vehicle_number = ""
		trans_doc_no = ""
		if self.transporter_id:
			transporter_id = self.transporter_id

		if self.trans_doc_date:
			trans_date = datetime.datetime.strptime(self.trans_doc_date, "%Y-%m-%d").strftime("%d/%m/%Y")
			
		if self.vehicle_number:
			vehicle_number = re.sub('[^A-Za-z0-9]+','',self.vehicle_number)

		if self.trans_doc_no:
			trans_doc_no = self.trans_doc_no

		billList = {
					'userGstin':self.from_addr.gst_no,
					'supplyType':self.supply_type,
					'subSupplyType':self.sub_type,
					'docType':'INV',
					'docNo':self.name,
					'docDate':invoice_date,
					'fromGstin':self.from_addr.gst_no,
					'fromTrdName':self.from_addr.name,
					'fromAddr1':self.from_addr.street,
					'fromAddr2':self.from_addr.street2,
					'fromPlace':self.from_addr.city_id.name.upper(),
					'fromPincode':int(self.from_addr.zip),
					'fromStateCode':int(self.from_addr.state_id.code),
					'actualFromStateCode':int(self.from_addr.state_id.code),
					'toGstin':self.to_addr.gst_no,
					'toTrdName':self.to_addr.name,
					'toAddr1':self.to_addr.street,
					'toAddr2':self.to_addr.street2,
					'toPlace':self.to_addr.city_id.name.upper(),
					'toPincode':int(self.to_zip_code),
					'toStateCode':int(self.to_addr.state_id.code),
					'actualToStateCode':int(self.to_addr.state_id.code),
					'totalValue':inv_total,
					'cgstValue':round(totalCgst,2),
					'sgstValue':round(totalSgst,2),
					'igstValue':round(totalIgst,2),
					'cessValue':round(totalCess,2),
					'transMode':self.transport_mode,
					'transDistance':self.transport_distance,
					'transporterName':self.transporter_name,
					'transporterId':transporter_id,
					'transDocNo':trans_doc_no,
					'transDocDate':trans_date,
					'vehicleNo':vehicle_number,
					'vehicleType':self.vehicle_type,
					'totInvValue':(inv_total + inv_tax),
					'mainHsnCode':int(hsn),
					'itemList':itemList
			}
		data = {'version':"1.0.0618",'billLists':billList}
		
		temp_json_file = tempfile.gettempdir()+'/file.json'
		# temp_json_file = "/tmp/Test.json"

		# = "C:\Users\NCPL\Desktop\Passport\Test.json"
		with open(temp_json_file, "w") as jsonFile:
			json.dump(data, jsonFile)

		file = open(temp_json_file, "rb")
		out = file.read()
		file.close()

		# if not self.to_addr.zip:
		# 	self.to_addr.write({'zip':self.to_zip_code})

		line_ids = []
				
		lr_id.write({'json_file': base64.b64encode(out), 'json_file_name':self.name+'.json'})