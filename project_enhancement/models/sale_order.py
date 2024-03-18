# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _,exceptions
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from collections import defaultdict


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    project_id = fields.Many2one('project.project','Project')


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    percentage = fields.Boolean()

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['percentage'] = self.percentage
        res['project_id'] = self.project_id.id
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        mo = self.env['mrp.production']
        order = False
        for rec in self:
            # Create a set to store already processed line IDs
            processed_lines = set()
            for line in rec.order_line:
                if line.product_id and line.id not in processed_lines:
                    bom = self.env['mrp.bom']._bom_find(
                        product=line.product_id,
                        company_id=rec.company_id.id,
                        bom_type='normal'
                    )
                    if bom:
                        picking_type = bom.picking_type_id if bom.picking_type_id else self.env[
                            'stock.picking.type'].search([
                            ('code', '=', 'mrp_operation'),
                            ('warehouse_id.company_id', '=', self.env.company.id),
                        ], limit=1)

                        order = mo.search([
                            ('sale_order_id', '=', rec.id),
                            ('product_id', '=', line.product_id.id),
                            ('state', '!=', 'cancel')
                        ], limit=1)

                        if not order:
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
                            # Perform necessary onchange methods and updates here
                            order.onchange_product_id()
                            order._onchange_bom_id()
                            order._onchange_move_finished()
                            order._onchange_workorder_ids()
                            order.product_qty = line.product_uom_qty
                            order._onchange_move_raw()
                            order._onchange_product_qty()
                            order._get_produced_qty()
                            order.write({'state': 'draft'})
                            order.write({'project_id': rec.project_id.id})
                            line.mo_id = order.id
                            processed_lines.add(line.id)

            # Send activity to purchase managers
            purchase_manager_group_id = self.env.ref('purchase.group_purchase_manager').id
            obj_group = self.env['res.groups'].sudo().search([('id', '=', purchase_manager_group_id)])
            obj_group_users = obj_group.users.mapped('id')

            if obj_group_users and order:
                for user in obj_group_users:
                    self.env['mail.activity'].create({
                        'summary': 'New MO',
                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                        'res_model_id': rec.env['ir.model']._get(mo._name).id,
                        'res_id': order.id,
                        'user_id': user
                    })

        return res

    def action_confirm_order(self):
        for rec in self:
            rec.action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    percentage = fields.Float()
    basic_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    remain_amount = fields.Monetary(compute='_compute_amount', string='Remain Amount', readonly=True, store=True)
    subtotal_from_remain = fields.Monetary(string='Subtotal From Remain', readonly=True, store=True)
    total_component_cost = fields.Float(string='Total Component Cost')
    total_operation_cost = fields.Float(string='Total Operation Cost')
    total_cost = fields.Float(string='Total Cost')

    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Invoice Status', compute='_compute_invoice_status', readonly=True, default='no')
    is_compute = fields.Boolean(compute='_compute_percentage')

    @api.onchange('product_id')
    def get_total_cost(self):
        for rec in self:
            rec.total_cost = rec.product_id.standard_price if rec.total_cost == 0 else rec.total_cost
    @api.depends('order_id.percentage', 'order_id.invoice_ids', 'product_id')
    def _compute_percentage(self):
        for line in self:
            if not line.is_compute and line.order_id.invoice_ids:  # Check if the method is not already being called
                if line.order_id.percentage and line.order_id.invoice_ids:
                    total_percentage = 0.0
                    for inv in line.order_id.invoice_ids:
                        product_lines = inv.invoice_line_ids.filtered(lambda il: il.product_id == line.product_id)
                        total_percentage += sum(product_lines.mapped('percentage'))
                    line.percentage = total_percentage
                    line.is_compute = True
                else:
                    line.percentage = 0.0
                    line.is_compute = False

    @api.constrains('percentage')
    def _percentage_validation(self):
        for rec in self:
            if rec.order_id.percentage:
                if (rec.percentage) > 100:
                    raise exceptions.ValidationError('Percentage Must Be 100 Or less')


    @api.depends('product_uom_qty','percentage', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            if line.order_id.percentage:
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'] * (line.percentage / 100),
                    'basic_subtotal': taxes['total_excluded'],
                    'remain_amount': taxes['total_excluded'] - taxes['total_excluded'] * (line.percentage / 100),
                })
            else:
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                    'basic_subtotal': taxes['total_excluded'],
                })

            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['basic_subtotal'] = self.basic_subtotal
        res['percentage'] = self.percentage
        res['remain_amount'] = self.remain_amount
        res['subtotal_from_remain'] = self.subtotal_from_remain
        # res['price_subtotal'] = self.price_subtotal
        if self.order_id.percentage and self.order_id.invoice_ids:
            res['percentage'] = 100 - self.percentage
        # res['analytic_account_id'] = analytic_account_id
        return res

    @api.depends('order_id.percentage','remain_amount')
    def _compute_invoice_status(self):
        super(SaleOrderLine, self)._compute_invoice_status()
        for line in self:
            if line.order_id.percentage and line.remain_amount != 0:
                line.invoice_status = 'to invoice'

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity','percentage')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        if line.order_id.percentage and line.percentage != 100:
                            qty_invoiced = 0.0
                        elif line.order_id.percentage and line.percentage == 100:
                            qty_invoiced = line.product_uom_qty
                        else:
                            qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
                                                                                          line.product_uom)
                    elif invoice_line.move_id.move_type == 'out_refund':
                        qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
                                                                                      line.product_uom)
            line.qty_invoiced = qty_invoiced

    qty_invoiced = fields.Float(
        compute='_get_invoice_qty', string='Invoiced Quantity', store=True, readonly=True,
        compute_sudo=True,
        digits='Product Unit of Measure')
