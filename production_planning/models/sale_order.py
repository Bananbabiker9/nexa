from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('customer_rank','>', 0)]", )

    state = fields.Selection(selection_add=[
        ('technical', 'Technical Office'),
        ('costing', 'Costing')
    ], )

    delivery_date = fields.Datetime('Delivery Date')

    def action_send_to_technical(self):
        return True

    def action_send_to_costing(self):
        return True

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        mo = self.env['mrp.production']
        for rec in self:
            for line in rec.order_line:
                if line.product_id:
                    bom = self.env['mrp.bom']._bom_find(product=line.product_id,
                                                        company_id=rec.company_id.id, bom_type='normal')
                    if bom:
                        picking_type = bom.picking_type_id if bom.picking_type_id else self.env['stock.picking.type'].search([
                            ('code', '=', 'mrp_operation'),
                            ('warehouse_id.company_id', '=', self.env.company.id),
                        ], limit=1)
                        order = mo.create({
                            'state': 'draft',
                            'is_production_planning': True,
                            'sale_order_id': rec.id,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom_id': line.product_uom.id,
                            'delivery_date': line.order_id.delivery_date,
                            'bom_id': bom.id,
                            'picking_type_id': picking_type.id,
                            'location_src_id': picking_type.default_location_src_id.id,
                            'location_dest_id': picking_type.default_location_dest_id.id
                        })
                        order.onchange_product_id()
                        order._onchange_bom_id()
                        order._onchange_move_finished()
                        order._onchange_workorder_ids()
                        order.product_qty = line.product_uom_qty
                        order._onchange_move_raw()
                        order._onchange_product_qty()
                        order._get_produced_qty()
                        order.write({'state': 'draft'})
                        line.mo_id = order.id
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mo_id = fields.Many2one('mrp.production', 'Manufacturing Order')

    def _get_protected_fields(self):
        res = super(SaleOrderLine, self)._get_protected_fields()
        return [
            'product_id', 'name', 'product_uom', 'product_uom_qty',
            'tax_id', 'analytic_tag_ids'
        ]