from odoo import api, fields, models, tools, SUPERUSER_ID, _


class Task(models.Model):
    _inherit = 'project.task'

    user_id = fields.Many2many('res.users', 'project_assigned_user_rel', string='Assigned to', index=True, tracking=True)
    user_email = fields.Char( string='User Email', readonly=True, related_sudo=False)

    @api.model
    def message_new(self, msg, custom_values=None):
        print('TEEEEEEEEEEEEEEEEEEEEEEEEEEEst')
        # pass

        return super(Task, self).message_new(msg, custom_values=custom_values)
