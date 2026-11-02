from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def _evaluate_product(
        self, closing_id, closing_line_id, last_close_date, product_id
    ):
        method = closing_id.force_evaluation_method
        if method in ("fifp", "lifp"):
            return self._get_cost_stock_move_lifo_fifo(
                closing_line_id, "fifo" if method == "fifp" else "lifo"
            )
        return super()._evaluate_product(
            closing_id, closing_line_id, last_close_date, product_id
        )
