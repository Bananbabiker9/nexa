from odoo import fields, models, api


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    production_plan = fields.Many2one('production.planning', related='production_id.production_plan', store=True)

