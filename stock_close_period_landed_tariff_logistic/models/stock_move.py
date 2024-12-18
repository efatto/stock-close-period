from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_additional_landed_cost_new(self, move_id, company_id):
        additional_landed_cost_new = super()._get_additional_landed_cost_new(
            move_id=move_id, company_id=company_id
        )
        # add tariff cost on country group
        price_unit = 0.0
        margin_percentage = 0.0
        if self.product_id.seller_ids:
            seller = self.product_id.seller_ids[0]
            margin_percentage += sum(
                seller.name.country_id.mapped(
                    "country_group_ids.logistic_charge_percentage"
                )
            )
            margin_percentage += seller.currency_id.change_charge_percentage
        if self.product_id.intrastat_code_id.tariff_id:
            margin_percentage += (
                self.product_id.intrastat_code_id.tariff_id.tariff_percentage
            )
        if margin_percentage:
            price_unit *= 1 + margin_percentage / 100.0
        additional_landed_cost_new += price_unit
        return additional_landed_cost_new
