{
    'name': 'Project Enhancement',
    'version': '14',
    'summary': 'Project Enhancement',
    'author': 'Next Era, Ahmed Abd El-Moniem <ahmed.abdelmoniem.1996@gmail.com>',
    'website': "My Company Website",
    'depends': ['project', 'mrp', 'cutting_list_items', 'production_planning', 'sale_project', 'sale','purchase','stock_landed_costs','mrp_bom_documents','so_bom_selection'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/project_project_views.xml',
        'views/product_template_view.xml',
        'views/mrp_pom_view.xml',
        'views/partner.xml',
        'views/project_task_view.xml',
        'views/sale_order.xml',
        'views/landed_cost.xml',
        'views/mrp_production.xml',

        'views/account_move.xml',
        'report/report.xml',
        'report/production_report.xml',
    ],
    'installable': True,
    'auto_install': False
}
