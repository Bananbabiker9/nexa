from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class POM(models.Model):
    _inherit = 'mrp.bom'

    pom_project_id = fields.Many2one('project.project', 'Project')
    total_component_cost = fields.Float(string='Total Component Cost', compute='_total_component_cost',store=True)
    total_operation_cost = fields.Float(string='Total Operation Cost', compute='_total_operation_cost',store=True)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        print("===", default)
        return super(POM, self).copy(default=default)


    def action_assign_project_pom(self):
        for rec in self:
            rec.write({'pom_project_id': self.env.context.get('default_pom_project_id')})

    def action_duplicate_pom(self):
        for rec in self:
            pom = rec.copy()
            pom.write({'pom_project_id': self.env.context.get('default_pom_project_id')})

    def action_view_select_bom(self):
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_bom_form_action")
        tree_view = [(self.env.ref('project_enhancement.bom_tree_view').id, 'tree')]
        # form_view = [(self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
        action['views'] = tree_view
        action['domain'] = [('pom_project_id', '=', False)]
        context = {
            'default_pom_project_id': self.env.context.get('default_pom_project_id'),
        }
        action['context'] = context
        return action
    #
    def action_generate_rfq(self):
        project_id = self.mapped('pom_project_id')
        lines = []
        for line in self:
            list_price = line.product_tmpl_id.price_compute('list_price')[line.product_tmpl_id.id]
            lines.append((0, 0, {
                'product_template_id': line.product_tmpl_id.id,
                'product_id': line.product_tmpl_id.product_variant_ids[0].id,
                'product_uom_qty': 1,
                'price_unit': list_price,
                'product_uom': line.product_tmpl_id.uom_id.id,
                'name': line.product_tmpl_id.display_name,
                'project_id': line.pom_project_id.id,
                'bom_id':line.id,
                'total_operation_cost': line.total_operation_cost,
                'total_component_cost': line.total_component_cost,
                'total_cost': line.total_component_cost + line.total_operation_cost,
            }))
        if self and lines:
            self.env['sale.order'].create({
                'project_id': project_id.id,
                'order_line': lines,
                'date_order': fields.Datetime.now(),
                'partner_id': project_id.partner_id.id
            })
        else:
            raise ValidationError(_('No BOMs selected.'))

    @api.depends('bom_line_ids')
    def _total_component_cost(self):
        for rec in self:
            total_component_cost = 0
            for line in rec.bom_line_ids:
                total_component_cost += line.product_id.standard_price * line.product_qty
            rec.total_component_cost = total_component_cost

    @api.depends('operation_ids')
    def _total_operation_cost(self):
        for rec in self:
            total_operation_cost = 0
            for line in rec.operation_ids:
                total_operation_cost += line.workcenter_id.costs_hour * (line.time_cycle/60)
            rec.total_operation_cost = total_operation_cost