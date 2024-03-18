# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def create_project_from_customer(self):
        self.ensure_one()
        project_obj = self.env['project.project']

        project_vals = {
            'name': self.name or '',
            'partner_id': self.id,
            'phone': self.phone or '',
            'email': self.email or '',
            #'analytic_account_id': self.default_analytic_account_id.id,
        }

        return {
            'name': 'Create Project',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'context': {
                'default_name': project_vals.get('name'),
                'default_partner_id': project_vals.get('partner_id'),
                'default_phone': project_vals.get('phone'),
                'default_email': project_vals.get('email'),
            },
            'target': 'new',
        }
class ProjectProject(models.Model):
    _inherit = 'project.project'

    date_of_creation = fields.Datetime(string="Date of Creation", related='create_date', readonly=True)
    delivery_date = fields.Datetime(string="Delivery to Customer")
    production_receipt_date = fields.Date(string="Date of Receipt and Production")
    product_types = fields.Char("نوع المنتج")
    customer_name = fields.Many2one("res.partner",string="العميل")
    address_name = fields.Char(string="العنوان")
    contract_date = fields.Date(string="تاريخ التعاقد")
    delivery_date = fields.Date(string="تاريخ التسليم")
    colors_codes = fields.Text(string="أكواد الألوان")
    internal_units = fields.Char(string="الوحدات الداخلية")
    thick = fields.Char(string="السمك")
    leaf_color = fields.Char(string="لون الضلف ")
    extra_code = fields.Char(string="الرمز الإضافي")
    wazar_color = fields.Char(string="لون الوازر")
    glass_sections_color = fields.Char(string="لون قطاعات الزجاج")
    handles_color = fields.Char(string="لون المقابض")
    glass_color = fields.Char(string="لون الزجاج")
    light_color = fields.Char(string="لون الإضاءة")
    company_name = fields.Char(string="اسم الشركة")
    hinges_type = fields.Char(string="نوع المفصلات")
    drawer_pull_type = fields.Char(string="نوع مقابض الأدراج")
    side = fields.Char(string="جانبي")
    lower = fields.Char(string="سفلي")
    handles_type = fields.Char(string="نوع المقابض")
    type = fields.Char(string="النوع")
    upper = fields.Char(string="علوي")
    blakar = fields.Char(string="بلاكار")
    notes_header2 = fields.Text(string="ملاحظات هامة")
