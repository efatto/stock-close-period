from odoo import models


class StockCloseReport(models.AbstractModel):
    _name = "report.stock_close_period_report.report_product_print"
    _description = "Stock Close Period Product Report"

    def _get_moves(self, close_line):
        # search the stock move in the same way of the current close period
        moves = self.env["stock.move"].search(
            [
                ("state", "=", "done"),
                ("product_qty", ">", 0),
                ("product_id", "=", close_line.product_id.id),
                ("date", ">", close_line.close_id.last_close_date),
                ("date", "<=", close_line.close_id.close_date),
                ("company_id", "=", close_line.close_id.company_id.id),
            ],
            order="date",
        )
        return moves

    def _get_report_values(self, docids, data=None):
        docs = self.env["stock.close.period"].browse(docids)
        return {
            "doc_ids": docs.ids,
            "doc_model": "stock.close.period",
            "docs": docs,
            "get_moves": self._get_moves,
        }
