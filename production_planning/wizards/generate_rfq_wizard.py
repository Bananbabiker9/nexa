from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class GenerateRFQWizard(models.TransientModel):
    _name = 'generate.rfq.wizard'

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    lines_ids = fields.One2many('generate.rfq.wizard.line', 'wizard_id', 'Lines')

    def action_generate_rfq(self):
        records = self.lines_ids
        missing_item = self.env['mrp.missing.item']
        mi_ids = records.mapped('missing_item_ids').ids
        items_list = []
        for item in records:
            items_list.append((0, 0, {
                'product_id': item.product_id.id,
                'mrp_qty_product': item.quantity,
                'mrp_product_uom': item.product_uom_id.id,
                'product_qty': item.product_uom_id._compute_quantity(item.quantity, item.product_id.uom_po_id),
                'product_uom': item.product_id.uom_po_id.id,
                'name': item.product_id.display_name,
                'date_planned': item.missing_item_ids[0].material_arrival_date if item.missing_item_ids[0].material_arrival_date else item.missing_item_ids[0].date
            }))
            if sum(missing.quantity for missing in item.missing_item_ids) > item.quantity:
                missing_item.create({
                    'mrp_order_id': item.missing_item_id.mrp_order_id.id if len(mi_ids) == 1 else False,
                    'product_id': item.product_id.id,
                    'quantity': sum(missing.quantity for missing in item.missing_item_ids) - item.quantity,
                    'product_uom_id': item.product_uom_id.id
                })
        if mi_ids and items_list:
            self.env['purchase.order'].create({
                'missing_item_ids': mi_ids,
                'order_line': items_list,
                'is_production_planning': True,
                'partner_id': self.partner_id.id

            })
            missing_items = self.env['mrp.missing.item'].search([('id', 'in', mi_ids)])
            missing_items.state = 'requested'
        else:
            raise ValidationError(_('No Missing items in selected orders.'))


class GenerateRFQWizardLine(models.TransientModel):
    _name = 'generate.rfq.wizard.line'

    wizard_id = fields.Many2one('generate.rfq.wizard')
    mrp_order_id = fields.Many2one(comodel_name="mrp.production", string="Production Order")
    product_id = fields.Many2one(comodel_name='product.product', required=True)
    quantity = fields.Float()
    product_uom_id = fields.Many2one(comodel_name='uom.uom', required=True)
    missing_item_ids = fields.Many2many(comodel_name="mrp.missing.item", string="Missing Items", store=True)