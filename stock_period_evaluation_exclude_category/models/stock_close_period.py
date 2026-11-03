from odoo import models


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    def _get_product_lines(self):
        res = super()._get_product_lines()
        if not self.no_recompute_lines:
            self.line_ids.filtered(
                lambda line: line.product_id.categ_id.exclude_from_stock_close_period
            ).unlink()
        return res
