

from odoo import api, fields, models,_


class Project(models.Model):
    _inherit = "res.partner"

    project_counter = fields.Integer(compute='_compute_project_counter')

    def action_open_project_wiz(self):
        return {
            'name': _('Project'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'context': {'default_partner_id': self.id},
            'target': 'new',
        }
    def _compute_project_counter(self):
        for rec in self:
            rec.project_counter = self.env['project.project'].search_count([('partner_id', '=', rec.id)])
