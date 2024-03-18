from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES,
                                 change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('supplier_rank','>', 0)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    missing_item_ids = fields.Many2many(comodel_name="mrp.missing.item", string="Missing Items", readonly=True)
    is_production_planning = fields.Boolean(default=False, readonly=True)

    def _prepare_picking(self):
        picking_vals = super(PurchaseOrder, self)._prepare_picking()
        picking_vals['purchase_order_id'] = self.id
        return picking_vals


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    mrp_qty_product = fields.Float(string='Alt. Quantity', digits='Product Unit of Measure')
    mrp_product_uom = fields.Many2one('uom.uom', string='Alt. UOM', domain="[('category_id', '=', product_uom_category_id)]")
    dimensions = fields.Boolean(related='product_id.dimensions',store=True)
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()

    @api.onchange('length', 'width', 'height')
    def compute_main_measure(self):
        for line in self:
            line.mrp_qty_product = round(line.width * line.height * line.length)

    @api.onchange('product_qty', 'product_uom', 'mrp_product_uom')
    def _onchange_product_qty(self):
        for rec in self:
            if rec.product_qty and rec.mrp_product_uom and rec.product_uom and rec.mrp_product_uom != rec.product_uom:
                rec.mrp_qty_product = rec.product_uom._compute_quantity(rec.product_qty, rec.mrp_product_uom)
                rec.product_uom = rec.mrp_product_uom
                rec.date_planned = fields.Date.today()

    @api.onchange('mrp_qty_product', 'mrp_product_uom')
    def _onchange_quantity(self):
        for rec in self:
            if rec.mrp_qty_product and rec.mrp_product_uom and rec.product_uom\
                    and rec.mrp_product_uom._compute_quantity(rec.product_qty, rec.product_uom) != rec.mrp_qty_product:
                rec.product_qty =  rec.mrp_product_uom._compute_quantity(rec.mrp_qty_product, rec.product_uom)# rec.product_uom._compute_quantity(rec.mrp_qty_product, rec.mrp_product_uom)
                rec.product_uom = rec.mrp_product_uom
                rec.date_planned = fields.Date.today()

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.product_id.dimensions:
            res['dimensions']= self.dimensions
            res['length']= self.length
            res['width']= self.width
            res['height']= self.height
            res['mrp_product_uom'] = self.mrp_product_uom
            res['mrp_qty_product']= self.mrp_qty_product
        return res