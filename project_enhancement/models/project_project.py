from odoo import fields, models, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    product_ids = fields.One2many('product.product', 'product_project_id', 'Products')
    pom_ids = fields.One2many('mrp.bom', 'pom_project_id', 'POMs')

    product_count = fields.Integer(compute='_get_products', readonly=True)
    pom_count = fields.Integer(compute='_compute_pom_count', readonly=True)
    quotation_count = fields.Integer(compute='_get_quotations', readonly=True)
    sale_count = fields.Integer(compute='_get_quotations', readonly=True)
    mrp_count = fields.Float('Manufacturing Orders Count', compute='_compute_mrp_count')
    expense_count = fields.Float('Expense Count', compute='_compute_invoice')
    invoice_count = fields.Float('Invoice Count', compute='_compute_invoice')
    vendor_bill_count = fields.Float('Vendor Count', compute='_compute_invoice')
    multi_user_id = fields.Many2many('res.users', string='Notified Users', tracking=True)

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.model
    def create(self, vals_list):
        res = super(ProjectProject, self).create(vals_list)
        if res.name and not res.analytic_account_id:
            project_analytic = self.env['account.analytic.account'].create({
                'name': res.name,
                'company_id': res.company_id.id,
            })
            res.analytic_account_id = project_analytic
        return res


    @api.depends('product_ids')
    def _get_products(self):
        for project in self:
            project.product_count = len(project.product_ids)

    def _get_quotations(self):
        for project in self:
            quotations = self.env['sale.order'].search([('project_id', '=', project.id), ('state', 'in', ('draft', 'sent'))])
            project.quotation_count = len(quotations)
            sale_orders = self.env['sale.order'].search([('project_id', '=', project.id), ('state', 'not in', ('draft', 'sent', 'cancel'))])
            project.sale_count = len(sale_orders)

    @api.depends('name')
    def _compute_invoice(self):
        for project in self:
            invoices = self.env['account.move'].search(
                [('project_id', '=', project.id), ('move_type', '=', 'out_invoice')])
            project.invoice_count = len(invoices)
            bills = self.env['account.move'].search(
                [('project_id', '=', project.id), ('move_type', '=', 'in_invoice')])
            project.vendor_bill_count = len(bills)
            bills = self.env['account.move'].search(
                [('project_id', '=', project.id), ('move_type', '=', 'entry')])
            project.expense_count = len(bills)

    @api.depends('name')
    def _compute_mrp_count(self):
        for project in self:
            orders = self.env['mrp.production'].search(
                [('project_id', '=', project.id),])
            project.mrp_count = len(orders)

    def action_view_products(self):
        products = self.mapped('product_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("product.product_normal_action_sell")
        action['domain'] = [('id', 'in', products.ids)]
        if not products:
            views = [(self.env.ref('project_enhancement.product_product_tree_view').id, 'tree'),
                     (self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
            # form_view = [(self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
            action['views'] = views
            action['domain'] = [('product_project_id', '=', False)]
        context = {
            'default_product_project_id': self.id,
        }
        action['context'] = context
        return action

    def action_view_bom(self):
        poms = self.mapped('pom_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_bom_form_action")
        action['domain'] = [('id', 'in', poms.ids)]
        if not poms:
            views = [(self.env.ref('project_enhancement.bom_tree_view').id, 'tree'),
                     (self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
            # form_view = [(self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
            action['views'] = views
            action['domain'] = []
        context = {
            'default_pom_project_id': self.id,
        }
        views = [(self.env.ref('mrp.mrp_bom_tree_view').id, 'tree'),
                 (self.env.ref('mrp.mrp_bom_byproduct_form_view').id, 'form')]
        # form_view = [(self.env.ref('project_enhancement.product_product_form_inherit').id, 'form')]
        action['views'] = views
        action['context'] = context
        return action

    def action_view_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations")
        action['domain'] = [('project_id', '=', self.id), ('state', 'in', ('draft', 'sent'))]
        context = {
            'default_project_id': self.id,
        }
        action['context'] = context
        return action

    def action_view_sale_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['domain'] = [('project_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'cancel'))]
        context = {
            'default_project_id': self.id,
        }
        action['context'] = context
        return action

    def action_view_bills(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action['domain'] = [('project_id', '=', self.id), ('move_type', '=', 'in_invoice')]
        context = {
            'default_project_id': self.id,
            'default_move_type': 'in_invoice',
        }
        action['context'] = context
        return action

    def action_view_expense(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        action['domain'] = [('project_id', '=', self.id), ('move_type', '=', 'entry')]
        context = {
            'default_project_id': self.id,
            'default_move_type': 'entry',
        }
        action['context'] = context
        return action

    def action_view_invoices(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('project_id', '=', self.id) ,('move_type', '=', 'out_invoice'),]
        context = {
            'default_project_id': self.id,
            'default_move_type': 'out_invoice',
        }
        action['context'] = context
        return action

    def action_view_mrp(self):
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        action['domain'] = [('project_id', '=', self.id) ]
        context = {
            'default_project_id': self.id,
        }
        action['context'] = context
        return action

    def action_view_cost_revenue(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Cost & Revenue',
            'res_model': 'mrp.production',
            'views': [(self.env.ref('project_enhancement.mrp_production_tree_view_totals').id, 'list')],
            'view_mode': 'list',
            'target': 'current',
            'domain': [('project_id', '=', self.id)],
        }
        return action

    def _compute_pom_count(self):
        for project in self:
            project.pom_count = len(project.pom_ids)
