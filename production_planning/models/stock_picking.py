from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    purchase_order_id = fields.Many2one(comodel_name="purchase.order")
    missing_item_ids = fields.Many2many(comodel_name="mrp.missing.item",
                                        related="purchase_order_id.missing_item_ids")


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, values):
        res = super(StockMove, self).write(values)
        if values.get('state') == 'done':
            for rec in self:
                picking = rec.picking_id
                if picking and picking.missing_item_ids and all(
                        move.state in ['cancel', 'done'] for move in picking.move_lines):
                    picking.missing_item_ids.state = 'delivered'
                    picking.missing_item_ids.mrp_order_id.action_assign()
        return res

    @api.model
    def create(self, values):
        res = super(StockMove, self).create(values)
        if res.state == 'done':
            picking = res.picking_id
            if picking and picking.missing_item_ids and all(
                    move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.missing_item_ids.state = 'delivered'
        return res
