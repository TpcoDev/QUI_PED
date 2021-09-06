# -*- coding: utf-8 -*-
{
    'name': "Website Dispatch Requests",

    'description': """
        Website Dispatch Requests
    """,

    'author': "TPCO",
    'website': "http://www.tpco.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website/Website',
    'version': '2.20210906.4',

    # any module necessary for this one to work correctly
    'depends': [
        'website', 'sale', 'portal',
        'sale_timesheet', 'sale_project', 'sale_stock', 'industry_fsm'
    ],

    # always loaded
    'data': [
        'security/dispatch_requests_security.xml',
        'views/res_users_views.xml',
        'views/assets.xml',
        'views/templates.xml',
        'views/project_task_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/sale_portal_templates.xml'

    ],
}
