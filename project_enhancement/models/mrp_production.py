from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class Valuation(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    production_id = fields.Many2one('mrp.production')
    cost_id = fields.Many2one(
        'stock.landed.cost', 'Landed Cost',
        ondelete='cascade', required=False)


class POM(models.Model):
    _inherit = 'mrp.production'

    valuation_lines = fields.One2many('stock.valuation.adjustment.lines','production_id', 'Project')

    total_component = fields.Float(string='Expected Component Cost', related='bom_id.total_component_cost',store=True)
    total_operation = fields.Float(string='Expected Operation Cost', related='bom_id.total_operation_cost',store=True)
    total_valuation = fields.Float(string='Expected Landed Cost', compute='_total_valuation_cost',store=True)
    total_expected = fields.Float(string='Expected Cost', compute='_total_expected_cost',store=True)
    total_actual = fields.Float(string='Actual Cost', related='product_id.standard_price',store=True)
    total_sale = fields.Float(string='Sale Cost', compute='_total_sale_cost',store=True)
    total_revenue = fields.Float(string='Total Revenue', compute='_total_revenue',store=True)
    document_count = fields.Integer(related='bom_id.document_count')
    @api.depends('valuation_lines')
    def _total_valuation_cost(self):
        for rec in self:
            rec.total_valuation = 0
            for line in rec.valuation_lines:
                rec.total_valuation += line.additional_landed_cost

    @api.depends('total_component','total_operation','total_valuation')
    def _total_expected_cost(self):
        for rec in self:
            rec.total_expected = rec.total_component + rec.total_operation + rec.total_valuation

    @api.depends('bom_id')
    def _total_sale_cost(self):
        for rec in self:
            sale_lines = self.env['sale.order.line'].search([('bom_id', '=', rec.bom_id.id), ('state', 'in', ('sale', 'done')), ('project_id', '=', rec.project_id.id)],limit=1)
            rec.total_sale = sale_lines.price_subtotal if sale_lines else 0
    @api.depends('total_actual','total_sale')
    def _total_revenue(self):
        for rec in self:
            rec.total_revenue = rec.total_sale - rec.total_actual

    def document_view(self):
        self.ensure_one()
        domain = [
            ('bom_ref', '=', self.bom_id.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'bom.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to Create for New Documents
                                </p>'''),
            'limit': 80,
            'context': "{'default_bom_ref': %s}" % self.id
        }