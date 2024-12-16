from odoo import fields, models


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    force_evaluation_method = fields.Selection(
        selection_add=[
            ("fifo", "Compute based FIFO"),
            ("lifo", "Compute based LIFO"),
        ],
        ondelete={'fifo': 'set default', 'lifo': 'set default'},
        help="Force Evaluation method will be used only for purchase costs computation.",
    )
