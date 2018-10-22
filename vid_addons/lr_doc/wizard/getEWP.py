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

REGISTERED = [('REG', 'Registered'),
			   ('UNREG', 'UnRegistered')]

class GetEwp(models.TransientModel):

	_name = "ewp.json"

	name = fields.Char('Doc Id', readonly=True)
	from_addr = fields.Many2one('res.partner', string="From Partner", readonly=True)
	to_addr = fields.Many2one('res.partner', string="To Partner", readonly=True)
	transport_mode = fields.Selection(DISPATCH_MODE, string="Transport Mode", default=1)
	supply_type = fields.Selection(SUPPLY_TYPE, string="Supply Type", default='O')
	sub_type = fields.Selection(SUB_TYPE, string="Sub Type", default=1)
	vehicle_type = fields.Selection(VEHICLE_TYPE, string="Vehicle Type", default="R")
	doc_type = fields.Selection(DOC_TYPE, string="Doc Type", default="INV")
	transport_distance = fields.Integer('Distance')
	transporter_name = fields.Char('Transporter Name')
	transporter_id = fields.Char('Transporter GST')
	trans_doc_no = fields.Char('Document Number')
	trans_doc_date = fields.Date('Document Date')
	vehicle_number = fields.Char('Vehicle Number')
	to_city = fields.Many2one("res.city", string="City", required=True)
	invoices_id = fields.Many2many("account.invoice", "ewb_invoices_rel", "partner_id", "invoice_id", string="Invoices", readonly=True)
	to_zip_code = fields.Char("To Zipcode", required=True)
	check_register = fields.Selection(REGISTERED, "GST")

	@api.model
	def default_get(self, fields):

		res = super(GetEwp, self).default_get(fields)
		invoices = []
		lr_id = self.env['lr.doc'].browse(self._context.get('active_ids', []))
		if lr_id:
			res['name'] = lr_id.name
			res['from_addr'] = lr_id.company_id.partner_id.id
			res['to_addr'] = lr_id.partner_id.id
			res['to_city'] = lr_id.city_id.id
			res['to_zip_code'] = lr_id.partner_id.zip
			for invoice in lr_id.invoice_id:
				invoices.append(invoice.id)
			res['invoices_id'] = [(6, 0, invoices)]
			res['transporter_name'] = lr_id.courier_name
			res['trans_doc_no'] = lr_id.docket_no
			res['trans_doc_date'] = lr_id.docket_date
			res['vehicle_number'] = lr_id.freight_no
			res['transporter_id'] = lr_id.transporter_gstin	
		return res
		
	@api.multi
	def get_json(self):

		billLists = []
		hsn_code_ids = self.env["hs.code"].search([])
		hsn_temp = []
	
		for invoice in self.invoices_id:
			item_no = 0
			item_list = OrderedDict()
			for line in invoice.invoice_line:
				hsn_cgst_total, hsn_sgst_total, hsn_igst_total, hsn_cess_total = 0, 0, 0, 0
				hsn_total_taxablevalue = 0
				
				hsn_total_taxablevalue += line.price_subtotal
				for tax in line.invoice_line_tax_id:
					if tax.gst_type == "cgst":
						hsn_cgst_total += round((line.price_subtotal * tax.amount), 2)
					elif tax.gst_type == "sgst":
						tax_percnt = (tax.amount * 2)*100
						val = "State"
						hsn_sgst_total = round((line.price_subtotal * tax.amount), 2)
					elif tax.gst_type == "igst":
						tax_percnt = (tax.amount)*100
						val = "Inter"
						hsn_igst_total = round((line.price_subtotal * tax.amount), 2)
					elif tax.gst_type == "cess":
						hsn_cess_total = round((line.price_subtotal * tax.amount), 2)
				if not item_list.has_key(line.product_id.hs_code_id.code[0:2]):
					item_list.update({line.product_id.hs_code_id.code[0:2]:{round(tax_percnt, 2):[round(hsn_total_taxablevalue, 2), round(hsn_igst_total, 2), round(hsn_sgst_total, 2), round(hsn_cgst_total, 2), round(hsn_cess_total, 2), line.quantity, val, line.product_id.hs_code_id.description]}})
				else:
					if not item_list[line.product_id.hs_code_id.code[0:2]].has_key(round(tax_percnt, 2)):
						item_list[line.product_id.hs_code_id.code[0:2]].update({round(tax_percnt, 2):[round(hsn_total_taxablevalue, 2), round(hsn_igst_total, 2), round(hsn_sgst_total, 2), round(hsn_cgst_total, 2), round(hsn_cess_total, 2), line.quantity, val, line.product_id.hs_code_id.description]})
					else:
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][0] += round(hsn_total_taxablevalue, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][1] += round(hsn_igst_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][2] += round(hsn_sgst_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][3] += round(hsn_cgst_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][4] += round(hsn_cess_total, 2)
						item_list[line.product_id.hs_code_id.code[0:2]][round(tax_percnt, 2)][5] += line.quantity

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

			invoice_date = datetime.datetime.strptime(invoice.date_invoice, "%Y-%m-%d").strftime("%d/%m/%Y")
			trans_date = ""
			transporter_id = ""
			vehicle_number = ""
			trans_doc_no = ""

			if self.check_register == 'UNREG' or self.sub_type == 2:
				toGSt = 'URP'
			else:
				toGSt = self.to_addr.gst_no
				
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
					'docNo':invoice.number.replace('SAJ-', ''),
					'docDate':invoice_date,
					'fromGstin':self.from_addr.gst_no,
					'fromTrdName':self.from_addr.name,
					'fromAddr1':self.from_addr.street,
					'fromAddr2':self.from_addr.street2,
					'fromPlace':self.from_addr.city_id.name.upper(),
					'fromPincode':int(self.from_addr.zip),
					'fromStateCode':int(self.from_addr.state_id.code),
					'actualFromStateCode':int(self.from_addr.state_id.code),
					'toGstin':toGSt,
					'toTrdName':self.to_addr.name or '',
					'toAddr1':self.to_addr.street or '',
					'toAddr2':self.to_addr.street2 or '',
					'toPlace':self.to_city.name.upper(),
					'toPincode':int(self.to_zip_code),
					'toStateCode':int(self.to_addr.state_id.code),
					'actualToStateCode':int(self.to_addr.state_id.code),
					'totalValue':invoice.amount_untaxed,
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
					'totInvValue':invoice.amount_total,
					'mainHsnCode':int(hsn),
					'itemList':itemList
				}
			billLists.append(billList)
		data = {'version':"1.0.0618",'billLists':billLists}
		
		temp_json_file = tempfile.gettempdir()+'/file.json'
		# temp_json_file = "/tmp/Test.json"

		# = "C:\Users\NCPL\Desktop\Passport\Test.json"
		with open(temp_json_file, "w") as jsonFile:
			json.dump(data, jsonFile)

		file = open(temp_json_file, "rb")
		out = file.read()
		file.close()

		if not self.to_addr.zip:
			self.to_addr.write({'zip':self.to_zip_code})

		line_ids = []

		record_set = self.env["lr.doc"].browse(self._context.get('active_ids'))
		record_set_line = self.env['lr.doc.line']

		# if not record_set.line_id:		
		# 	for line in self.invoices_id:
		# 		line_id = record_set_line.create({'invoice_id':line.id, 'lr_id':record_set.id})
		# 		line_ids.append(line_id.id)
		# 	record_set.write({'line_id':[(6, 0, line_ids)]})
				
		record_set.write({'json_file': base64.b64encode(out), 'json_file_name':self.name+'.json', 'state':'validate'})