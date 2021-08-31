# -*- coding: utf-8 -*-
{
    'name': "Fleet Additionals",
    
    'description': """
        
    """,
    
    'author': "TPCO",
    'website': "http://www.tpco.com",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Fleet',
    'version': '1.0.2021.08.31',
    
    # any module necessary for this one to work correctly
    'depends': ['fleet', 'website_dispatch_requests'],
    
    # always loaded
    'data': [

        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',
        'views/remolque_dia_views.xml',
        'views/project_task_views.xml',
        'views/asiganr_remolque_views.xml',

        'report/report_project_task_planned.xml',
        # 'report/report_project_task_cargo.xml',
    
    ],
}