# -*- coding: utf-8 -*-
{
    'name': "custom sales project",

    'summary': """
        custom sales project""",

    'description': """
        custom sales project
    """,

    'author': "Mathany Nimer",
    'website': "http://www.nextrabd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'project', 'mrp'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/sale_partner_inherit.xml',
        'views/project_inherit.xml',
        'views/project_kanban.xml',
    ],
}
