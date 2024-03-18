from odoo import fields, models, api
from odoo import models, fields, api, exceptions,_
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError



class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one('project.project','Project')
    percentage = fields.Boolean()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    percentage = fields.Float()
    basic_subtotal = fields.Monetary(string='Basic Subtotal', readonly=True, store=True)
    remain_amount = fields.Monetary(string='Remain Amount', readonly=True, store=True)
    subtotal_from_remain = fields.Monetary(string='Subtotal From Remain', readonly=True, store=True)

    @api.constrains('percentage')
    def _percentage_validation(self):
        for rec in self:
            if rec.move_id.percentage:
                if (rec.percentage) > 100:
                    raise exceptions.ValidationError('Percentage Must Be 100 Or less')

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        res = {}
        if self.move_id.percentage:
            # self.price_unit = self.basic_subtotal / quantity
            line_discount_price_unit = self.basic_subtotal / quantity * (1 - (discount / 100.0))
        else:
            # Compute 'price_subtotal'.
            line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
                                                                             quantity=quantity, currency=currency,
                                                                             product=product, partner=partner,
                                                                             is_refund=move_type in (
                                                                                 'out_refund', 'in_refund'))
            if self.move_id.percentage:
                if self.percentage > 0:
                    price_subtotal = taxes_res['total_excluded'] * (self.percentage / 100)
                elif self.percentage == 0:
                    price_subtotal = 0
                # Calculate unit price proportionally based on the updated subtotal
                self.price_unit = price_subtotal / quantity
            else:
                price_subtotal = taxes_res['total_excluded']
            res['price_subtotal'] = price_subtotal
            res['price_total'] = taxes_res['total_included']
        else:
            if self.move_id.percentage:
                if self.percentage > 0:
                    res['price_subtotal'] = subtotal * (self.percentage / 100)
                    # Calculate unit price proportionally based on the updated subtotal
                    self.price_unit = res['price_subtotal'] / quantity
                elif self.percentage == 0:
                    res['price_subtotal'] = 0
                    res['price_unit'] = 0
                    # self.price_unit = res['price_subtotal']
                    # raise exceptions.ValidationError(self.price_unit)
            else:
                res['price_total'] = res['price_subtotal'] = subtotal

        # In case of multi currency, round before it's used for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=self.price_unit if price_unit is None else price_unit,
            quantity=self.quantity if quantity is None else quantity,
            discount=self.discount if discount is None else discount,
            currency=self.currency_id if currency is None else currency,
            product=self.product_id if product is None else product,
            partner=self.partner_id if partner is None else partner,
            taxes=self.tax_ids if taxes is None else taxes,
            move_type=self.move_id.move_type if move_type is None else move_type,
        )

