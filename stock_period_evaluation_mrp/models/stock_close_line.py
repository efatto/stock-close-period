# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class StockClosePeriodLineInherit(models.Model):
    _inherit = "stock.close.period.line"

    evaluation_method = fields.Selection(selection_add=[("production", "Production")])

    def action_recalculate_production(self):
        for line in self:
            if not line.close_id.bypass_negative_qty and line.product_qty < 0:
                raise UserError(
                    _(
                        "It's not possible to continue the execution."
                        "This product have quantity < 0."
                    )
                )

            self.env["stock.move.line"].recompute_average_cost_period_production(
                line.close_id, line
            )
            line.close_id.work_end = fields.Datetime.now()
        return True
