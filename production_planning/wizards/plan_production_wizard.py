from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta


class ProductionPlanningWizard(models.TransientModel):
    _name = 'production.planning.wizard'

    name = fields.Char('Name')
    start = fields.Datetime('From')
    end = fields.Datetime('To')
    mrp_production_ids = fields.Many2many('mrp.production', string='Production Orders',)
    existing = fields.Boolean()

    @api.onchange('start')
    def _get_end_date(self):
        for rec in self:
            end_date = False
            mrps = self.env.context.get('default_mrp_production_ids')
            max_duration = self.env['mrp.production'].get_workorder_duration(mrps)
            if rec.start:
                end_date = rec.start + relativedelta(minutes=max_duration)
            rec.end = end_date

    def action_plan(self):
        if self.existing:
            plan = self.env['production.planning'].browse(self.env.context.get('plan_id'))
        else:
            plan = self.env['production.planning'].create({'name': self.name,
                                                           'start': self.start,
                                                           'end': self.end,
                                                           'mrp_production_ids': self.mrp_production_ids.ids})
        start = self.start
        mrp_production_ids = self.mrp_production_ids.sorted(key=lambda r: r.sequence)
        for order in mrp_production_ids:
            order.write({'production_plan': plan.id,
                         'date_planned_start': start,
                         'date_planned_finished': self.end})
            (order.move_raw_ids | order.move_finished_ids).filtered(lambda m: m.state == 'draft')._action_confirm()
            order._plan_workorders(replan=True)
            start = order.date_planned_finished
        # plan.end = start
        return True

