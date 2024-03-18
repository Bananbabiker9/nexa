from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection(selection_add=[
        ('technical', 'Technical Office'),
        ('costing', 'Costing')
    ], )

    is_production_planning = fields.Boolean(default=False, readonly=True)
    sale_order_id = fields.Many2one(comodel_name="sale.order", readonly=True)
    production_plan = fields.Many2one('production.planning', readonly=True)
    delivery_date = fields.Datetime('Delivery Date')
    material_arrival_date = fields.Datetime('Material Arrival Date')
    sequence = fields.Integer('Seq', default=1)

    def action_send_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_send_to_technical(self):
        for rec in self:
            rec.write({'state': 'technical'})

    def action_send_to_costing(self):
        for rec in self:
            rec.write({'state': 'costing'})

    def action_generate_missing_items(self):
        records = self.filtered(lambda self: self.is_production_planning and self.state == 'draft')
        if not records:
            raise ValidationError(_(' No Available Draft Production Planning Orders from the selected ones or its not production planning.'))
        missing_item = self.env['mrp.missing.item']
        for order in records:
            order.action_confirm()
            order.action_assign()
            for line in order.move_raw_ids:
                if line.product_uom_qty != line.forecast_availability:
                    missing_item.create({
                        'mrp_order_id': order.id,
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                        'product_uom_id': line.product_uom.id,
                        'delivery_date': order.delivery_date,
                        'material_arrival_date': order.material_arrival_date,
                    })

    def get_workorder_duration(self, mrp):
        mrps = self.browse(mrp)
        max_duration = 0
        for order in mrps:
            for workorder in order.workorder_ids:
                max_duration += workorder._get_duration_expected()
        return max_duration

    def action_plan_production_order(self):
        records = self.filtered(lambda self: self.is_production_planning and not self.production_plan)
        if not records:
            raise ValidationError(_('All the selected Production Orders are planned.'))
        return {
            'name': _('Plan Production Orders'),
            'view_mode': 'form',
            'res_model': 'production.planning.wizard',
            'view_id': self.env.ref('production_planning.plan_production_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_mrp_production_ids': sorted(records.ids)},
            'target': 'new'
        }

    def action_unplan_production_order(self):
        records = self.filtered(lambda self: self.is_production_planning and self.production_plan)
        if not records:
            raise ValidationError(_('All the selected Production Orders are planned.'))
        for production in records:
            production.production_plan = False
            # production.button_unplan()

    def action_correct_operations(self):
        for rec in self:
            rec._onchange_product_qty()

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        if self.production_plan:
            # plan_mrps = self.production_plan.mrp_production_ids
            planed_duration = self.get_workorder_duration(self.id)
            real_duration = sum(x.duration for x in self.workorder_ids)
            # end_date = self.production_plan.start + relativedelta(minutes=max_duration)
            if real_duration > planed_duration:
                self.production_plan.is_delayed = True
                delta = relativedelta(real_duration - planed_duration)
                hours = delta.hours
                minutes = delta.minutes
                seconds = delta.seconds
                waiting_time = str(hours) + " h " + str(minutes) + " m " + str(seconds) + " S "
                if not self.production_plan.reason:
                    self.production_plan.reason = 'Reason '
                self.production_plan.reason += ' Order #: %s  Delayed By: %s \n' % (self.name, waiting_time)
                self.production_plan.end += delta
        return res