from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception,content_disposition
import base64

class Binary(http.Controller):

	@http.route('/web/binary/docu_down', type='http', auth="public")
	@serialize_exception
	def docu_down(self, data, filename):

		return request.make_response(data,
                            [('Content-Type', 'application/json'),
                             ('Content-Disposition', content_disposition(filename))]) 
