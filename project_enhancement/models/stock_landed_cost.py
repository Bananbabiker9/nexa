from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    project_id = fields.Many2one('project.project', 'Project')

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.mrp_production_ids = self.mrp_production_ids.search(
                [('project_id', '=', self.project_id.id),]).ids
            # self.write({'mrp_production_ids': [[4, mo, 0] for mo in mrp_production_ids]})

    def button_validate(self):
        res = super(LandedCost,self).button_validate()
        self._create_production_valuation()
        return res
    def _create_production_valuation(self):
        product_id = False

        for line in self.valuation_adjustment_lines:
            if line.product_id != product_id:
                product_id = line.product_id.id
                for production in self.mrp_production_ids:
                    self.env['stock.valuation.adjustment.lines'].create({
                        'cost_line_id': line.cost_line_id.id,
                        'quantity': line.quantity,
                        'additional_landed_cost': line.additional_landed_cost,
                        'product_id': line.product_id.id,
                        'production_id': production.id,
                    })

