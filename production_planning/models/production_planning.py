from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta


class ProductionPlanning(models.Model):
    _name = 'production.planning'

    name = fields.Char('Name', )
    start = fields.Datetime('From')
    end = fields.Datetime('To')
    mrp_production_ids = fields.One2many('mrp.production', 'production_plan', string='Production Orders')
    is_delayed = fields.Boolean('Is delayed')
    reason = fields.Text('Delay Reason')

    def button_plan_production_order(self):
        return {
            'name': _('Plan Production Orders'),
            'view_mode': 'form',
            'res_model': 'production.planning.wizard',
            'view_id': self.env.ref('production_planning.plan_production_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_mrp_production_ids': sorted(self.mrp_production_ids.ids), 'default_existing': True,
                        'default_name': self.name, 'default_start': self.start, 'plan_id': self.id},
            'target': 'new'
        }

    def _get_end_date(self):
        for rec in self:
            end_date = False
            mrps = self.mrp_production_ids
            max_duration = self.env['mrp.production'].get_workorder_duration(mrps)
            if rec.start:
                end_date = rec.start + relativedelta(minutes=max_duration)
            rec.end = end_date