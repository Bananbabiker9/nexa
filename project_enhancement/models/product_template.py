from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_project_id = fields.Many2one('project.project', 'Project')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        print("===", default)
        return super(ProductTemplate, self).copy(default=default)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_project_id = fields.Many2one('project.project', 'Project')

    def action_assign_project_product(self):
        for rec in self:
            rec.write({'product_project_id': self.env.context.get('default_product_project_id')})

    def action_duplicate_product(self):
        for rec in self:
            product = rec.copy()
            product.write({'product_project_id': self.env.context.get('default_product_project_id')})

    def action_view_select_product(self):
        action = self.env["ir.actions.actions"]._for_xml_id("product.product_normal_action_sell")
        tree_view = [(self.env.ref('project_enhancement.product_product_tree_view').id, 'tree')]
        # form_view = [(self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
        action['views'] = tree_view
        action['domain'] = [('product_project_id', '=', False)]
        context = {
            'default_product_project_id': self.env.context.get('default_product_project_id'),
        }
        action['context'] = context
        return action

    def action_generate_rfq(self):
        project_id = self.mapped('product_project_id')
        lines = []
        for product in self:
            lines.append((0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
                'product_uom': product.uom_id.id,
                'name': product.display_name,
                'project_id': product.product_project_id.id
            }))
        if self and lines:
            self.env['sale.order'].create({
                'project_id': project_id.id,
                'order_line': lines,
                'partner_id': project_id.partner_id.id
            })
        else:
            raise ValidationError(_('No Product selected.'))