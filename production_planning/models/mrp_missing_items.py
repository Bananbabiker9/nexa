from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MrpMissingItem(models.Model):
    _name = 'mrp.missing.item'

    name = fields.Char(readonly=True)
    date = fields.Date(default=lambda self: fields.Date.today())
    delivery_date = fields.Datetime('Delivery Date')
    material_arrival_date = fields.Datetime('Material Arrival Date')
    mrp_order_id = fields.Many2one(comodel_name="mrp.production", string="Production Order")
    mrp_plan = fields.Many2one('production.planning', readonly=True, related='mrp_order_id.production_plan')
    product_id = fields.Many2one(comodel_name='product.product', required=True)
    quantity = fields.Float()
    product_uom_id = fields.Many2one(comodel_name='uom.uom', required=True)
    state = fields.Selection([
        ('draft', 'Missing'),
        ('requested', 'Requested'),
        ('delivered', 'Delivered')
    ], default='draft')

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code("mrp.missing.items.code")
        return super(MrpMissingItem, self).create(values)

    def action_generate_rfq(self):
        records = self.filtered(lambda self: self.state in ['draft', 'requested'])
        if not records:
            raise ValidationError(_('No Available Draft Missing items from the selected ones.'))
        mi_ids = records.ids
        items_list = []
        products_list = []
        for item in records:
            if item.product_id.id not in products_list:
                product_lines = records.filtered(lambda t: t.product_id == item.product_id)
                qty = sum(p_line.quantity for p_line in product_lines)
                items_list.append((0, 0, {
                    'product_id': item.product_id.id,
                    'quantity': qty,
                    'product_uom_id': item.product_uom_id.id,
                    'mrp_order_id': item.mrp_order_id.id,
                    'missing_item_ids': product_lines.ids
                }))
                products_list.append(item.product_id.id)
        if mi_ids and items_list:
            return {
                'name': _('Generate RFQ'),
                'view_mode': 'form',
                'res_model': 'generate.rfq.wizard',
                'view_id': self.env.ref('production_planning.generate_rfq_wizard_view_form').id,
                'type': 'ir.actions.act_window',
                'context': {'default_lines_ids': items_list},
                'target': 'new'
            }
        else:
            raise ValidationError(_('No Missing items in selected orders.'))
