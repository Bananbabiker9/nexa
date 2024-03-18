from odoo import fields, models, api, _


class SelectPlanWizard(models.TransientModel):
    _name = 'select.plan.wizard'

    plan_id = fields.Many2one('production.planning', required=True)
    start = fields.Datetime('From', related='plan_id.start')
    end = fields.Datetime('To', related='plan_id.end')

    def action_plan(self):
        return {
            'name': _('Plan Production Orders'),
            'view_mode': 'tree,kanban,form,calendar,pivot,graph',
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('production_planning.mrp_production_tree_view_2').id, 'tree'),
                      (self.env.ref('mrp.mrp_production_form_view').id, 'form')],
            'domain': [('production_plan', '=', self.plan_id.id)],
        }
