from odoo import fields, models
from odoo.tools import get_lang
from odoo.tools.float_utils import float_round


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    force_evaluation_method = fields.Selection(
        selection_add=[
            ("fifo", "Compute based FIFO"),
            ("lifo", "Compute based LIFO (continuos)"),
            # ("lifp", "Compute based LIFO (periodic)"),
        ],
        ondelete={"fifo": "set default", "lifo": "set default"},
        help="Force Evaluation method will be used only for purchase costs computation.",
    )


class StockClosePeriodLine(models.Model):
    _inherit = "stock.close.period.line"

    evaluation_details = fields.Text(string="Evaluation Details")

    def _format_value(self, value):
        lang = get_lang(self.env, lang_code=self.company_id.partner_id.lang)
        amount = float_round(
            value, precision_rounding=self.company_id.currency_id.rounding
        )
        amount_formatted = lang.format(
            "%.2f",
            amount,
            grouping=True,
            monetary=True,
        )
        return amount_formatted
