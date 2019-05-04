# -*- coding: utf-8 -*-
{
    'name': "Email Config",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VIDTS",
    'website': "http://www.vidts.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Email Outgoing Server',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_setup', 'hr', 'hr_holidays', 'report_xls', 'hr_gamification'],

    # always loaded
    'data': [
        'views/partner_email_config.xml',
        'views/smtp_config_views.xml',
        'views/retirement_age_view.xml',
        'views/leave_summary.xml',
        'wizard/leave_report_views.xml',
        'report/leave_summary_view.xml',
        'data/hr_workflow.xml'
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],

    'application':True
}