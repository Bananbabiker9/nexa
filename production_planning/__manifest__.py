{
    'name': 'Production Planning',
    'version': '14',
    'summary': 'Production Planning',
    'author': 'Next Era, Dalia Atef <dahliaatef@gmail.com>',
    'website': "My Company Website",
    'depends': ['mrp', 'sale_purchase', 'purchase_stock', 'mrp_workorder','inventory_enhancement'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/mrp_missing_items.xml',
        'views/mrp_production.xml',
        'views/purchase_order.xml',
        'views/mrp_workorder_views.xml',
        'views/sale_order_views.xml',
        'views/production_planning_views.xml',
        'views/menu.xml',
        'wizards/plan_production_wizard_view.xml',
        'wizards/generate_rfq_wizard_view.xml',
        'wizards/select_plan_wizard.xml',
    ],
    'installable': True,
    'auto_install': False
}
