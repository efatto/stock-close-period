from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import get_lang
from odoo.tools.float_utils import float_round


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    force_evaluation_method = fields.Selection(
        selection_add=[
            ("fifo", "Compute based FIFO"),
            ("lifo", "Compute based LIFO (continuos)"),
            ("lifp", "Compute based LIFO (periodic)"),
        ],
        ondelete={"fifo": "set default", "lifo": "set default"},
        help="Force Evaluation method will be used only for purchase costs computation."
        "FIFO: with FIFO logic;"
        "LIFO (continuos): with LIFO logic from the beginning of the moves (require "
        "that a previous closing is not set);"
        "LIFO (periodic): with LIFO logic from the previous closing (require that a "
        "previous closing is set).",
    )

    @api.constrains("force_evaluation_method")
    def _check_force_evaluation_method(self):
        for closing in self:
            if closing.force_evaluation_method == "lifo" and closing.last_closed_id:
                raise UserError(_("You can't set a previous closing."))
            if closing.force_evaluation_method == "lifp" and not closing.last_closed_id:
                raise UserError(_("You must set a previous closing."))


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
