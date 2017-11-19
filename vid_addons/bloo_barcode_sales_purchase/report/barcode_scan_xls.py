# -*- coding: utf-8 -*-
from openerp.addons.report_xls.report_xls import report_xls
import xlwt


class loom_report_xls(report_xls):
    def generate_xls_report(self, _p, _xs, data, objects, wb):
        print "ddddddddddddddddddddd", data
        report_name = "Barcode Scan"
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 1
        ws.fit_width_to_pages = 1
        row_pos = 0
        ws.set_horz_split_pos(row_pos)
        row_pos += 1
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        print "vvvvvvvvvvvvvvvvvvvvvvvv", objects
        _xs.update({
            'xls_title': 'font: bold true, height 350;'
        })
        _xs.update({
            'xls_sub_title': 'font: bold true, height 300;'
        })
        _myxs = {'borders': 'borders: ' 'top thin, bottom thin',
                 'top_bottom_lined': 'borders: ' 'top medium, bottom thin',
                 }
        cell_style = xlwt.easyxf(_xs['xls_title'] + _xs['center'])
        cell_center = xlwt.easyxf(_xs['center'])
        cell_center_bold_no = xlwt.easyxf(_xs['center'] + _xs['bold'])
        cell_center_bold = xlwt.easyxf(_xs['center'] + _xs['bold'] + _myxs['top_bottom_lined'])
        cell_left = xlwt.easyxf(_xs['left'])
        cell_left_b = xlwt.easyxf(_xs['left'] + _xs['bold'])
        print "aaaaaaaaaaaaaaaaaaaaaaaaaa"
        # c_specs = [('report_name', 8, 0, 'text', report_name)]
        # row_data = self.xls_row_template(c_specs, ['report_name'])
        # row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
        ws.row(row_pos - 1).height_mismatch = True
        ws.row(row_pos - 1).height = 220 * 2
        # row_pos += 1
        # get_line = _p.get_lines(data['form']['based_on'], data['form']['company_id'], data['form']['chart_tax_id'])
        # top2 = [('entry1', 3, 0, 'text', str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M %p")))]
        # row_data = self.xls_row_template(top2, [x[0] for x in top2])
        # row_pos = self.xls_write_row(ws, row_pos, row_data, cell_left_b)
        # row_pos += 1
        print "aaaaaaaaaaaaaaaaaaaaaaaaaa", objects.move_lines
        # top_ev_1 = [('entry1', 4, 0, 'number', 1),
        #             ('entry2', 1, 0, 'number', 1),
        #             ('entry3', 1, 0, 'number', 1),
        #             ('entry4', 2, 0, 'number', 1)]
        # row_data = self.xls_row_template(top_ev_1, [x[0] for x in top_ev_1])
        # row_pos = self.xls_write_row(ws, row_pos, row_data, cell_center)
        for each in objects.move_lines:
            top_ev_1 = [('entry1', 2, 0, 'number', objects.id),
                        ('entry2', 2, 0, 'number', each.product_id.default_code),
                        ('entry3', 2, 0, 'text', each.product_id.name),
                        ('entry4', 2, 0, 'number', each.product_uom_qty)]
            row_data = self.xls_row_template(top_ev_1, [x[0] for x in top_ev_1])
            row_pos = self.xls_write_row(ws, row_pos, row_data, cell_left)


loom_report_xls('report.barcode.report_xls', 'stock.picking')
