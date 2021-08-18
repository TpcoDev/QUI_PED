# -*- coding: utf-8 -*-
{
    'name': "Website Dispatch Requests",
    
    'description': """
        Long description of module's purpose
    """,
    
    'author': "TPCO",
    'website': "http://www.yourcompany.com",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website/Website',
    'version': '1.20210817',
    
    # any module necessary for this one to work correctly
    'depends': ['website', 'sale_timesheet', 'sale_project', 'industry_fsm', 'stock'],
    
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/templates.xml',
        'views/project_task_views.xml',
        'views/res_partner_views.xml'
    
    ],
}
