from odoo import models


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    def _get_products(self):
        super()._get_products()
        return (
            self.env["product.product"]
            .with_context(active_test=False)
            .search(
                [
                    ("type", "!=", "service"),
                    ("categ_id.exclude_from_stock_close_period", "!=", True),
                ]
            )
        )
