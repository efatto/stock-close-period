# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class StockClosePeriod(models.Model):
    _name = "stock.close.period"
    _description = "Stock Close Period"

    name = fields.Char(
        string="Reference",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
    )
    line_ids = fields.One2many(
        "stock.close.period.line",
        "close_id",
        string="Product",
        copy=True,
        readonly=False,
        states={"done": [("readonly", True)]},
    )
    state = fields.Selection([
        ("draft", "Draft"),
        ("confirm", "In Progress"),
        ("done", "Validated"),
        ("cancel", "Cancelled")
    ], copy=False, index=True, readonly=True, default="draft", string="Status")
    close_date = fields.Date(
        readonly=True,
        required=True,
        default=fields.Date.context_today,
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
        help="The date that will be used for the store the product quantity and average cost.",
    )
    amount = fields.Float(string="Stock Amount Value", readonly=True, copy=False)
    work_start = fields.Datetime(readonly=True, default=fields.Datetime.now)
    work_end = fields.Datetime(readonly=True)
    force_evaluation_method = fields.Selection([
        ("no_force", "Compute based category setup"),
        ("purchase", "Compute based purchase average cost"),
        ("standard", "Compute based cost in product")
    ], default="no_force", copy=False, help="Force Evaluation method will be used only for compute purchase costs.")
    last_closed_id = fields.Many2one(
        "stock.close.period",
        string="Last Closed",
        copy=False,
        states={"done": [("readonly", True)]},
    )
    force_archive = fields.Boolean(
        default=False,
        help="Marks as archive the inventory move lines used during the process.",
    )
    purchase_ok = fields.Boolean(default=False, readonly=True, help="Marks if action 'Compute Purchase' is processed.")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    def unlink(self):
        for closing in self:
            if closing.state in ["confirm", "done"]:
                raise UserError(_(
                    "State in '%s'. You can only delete in state 'Draft' or 'Cancelled'." % closing.state
                ))
        return super(StockClosePeriod, self).unlink()

    def action_set_to_draft(self):
        for closing in self:
            if closing.state == "cancel":
                # clear data
                closing.line_ids.unlink()
                closing.state = "draft"
                closing.amount = 0
                closing.purchase_ok = False

    def _get_product_lines(self):
        self.ensure_one()

        # add all products active not services type
        query = """
            INSERT INTO 
                stock_close_period_line(
                    close_id,
                    product_id,
                    product_code,
                    product_name,
                    product_uom_id,
                    categ_name,
                    product_qty,
                    price_unit,
                    company_id
                )
            SELECT
                %r AS close_id,
                product_product.id AS product_id,
                product_template.default_code AS product_code,
                product_template.name AS product_name,
                product_template.uom_id AS product_uom,   
                product_category.complete_name AS complete_name,
                0 AS product_qty,
                0 AS price_unit,
                %r AS company_id
            FROM
                product_template,
                product_product,
                product_category
            WHERE
                product_template.type != 'service' 
                AND product_product.product_tmpl_id = product_template.id 
                AND product_template.categ_id = product_category.id 
                AND (
                    product_template.company_id = %r 
                    OR product_template.company_id IS NULL
                )
            ORDER BY
                product_product.id;
        """ % (self.id, self.company_id.id, self.company_id.id)
        self.env.cr.execute(query)

        # get quantity on end period for each product
        for closing_line_id in self.line_ids:
            product_id = closing_line_id.product_id
            list_product_qty = product_id._compute_qty_available(self.close_date)
            count = 0
            for line in list_product_qty:
                if count == 0:
                    closing_line_id.product_qty = line["stock_at_date"]
                    closing_line_id.location_id = line["location_id"]
                    closing_line_id.lot_id = line["lot_id"]
                    closing_line_id.owner_id = line["owner_id"]
                else:
                    self.env["stock.close.period.line"].create({
                        "close_id": self.id,
                        "product_id": line["product_id"],
                        "product_uom_id": line["uom_id"],
                        "product_qty": line["stock_at_date"],
                        "location_id": line["location_id"],
                        "lot_id": line["lot_id"],
                        "owner_id": line["owner_id"],
                        "price_unit": 0
                    })
                count += 1

    def action_start(self):
        for closing in self.filtered(lambda x: x.state not in ("done", "cancel")):
            # add product line
            closing._get_product_lines()
            # set confirm status
            closing.state = "confirm"
        return True

    def _check_qty_available(self):
        self.ensure_one()

        # if a negative value, can't continue
        negative = self.line_ids.filtered(lambda x: x.product_qty < 0)
        if negative:
            res = False
        else:
            res = True
        return res

    def _deactivate_moves(self):
        self.ensure_one()

        # set active = False on stock_move and stock_move_line
        query = """
            UPDATE 
                stock_move
            SET 
                active = false 
            WHERE
                date <= date(%r) 
                AND state = 'done' 
                AND (
                    company_id == %r 
                    OR company_id IS NULL
                );
        """ % (self.close_date, self.company_id.id)
        self.env.cr.execute(query)

        query = """
            UPDATE 
                stock_move_line 
            SET 
                active = false 
            WHERE
                date <= date(%r) 
                AND state = 'done' 
                AND (
                    company_id == %r 
                    OR company_id IS NULL
                );
        """ % (self.close_date, self.company_id.id)
        self.env.cr.execute(query)
        return True

    def action_recalculate_purchase(self):
        for closing in self:
            if not closing._check_qty_available():
                raise UserError(_("Is not possible continue the execution. There are product with quantities < 0."))

            self.env["stock.move.line"].recompute_average_cost_period_purchase(closing)
            closing.purchase_ok = True
            if closing.force_archive:
                closing._deactivate_moves()
            closing.work_end = datetime.now()
        return True

    def action_cancel(self):
        for closing in self:
            closing.state = "cancel"
        return True

    def action_force_done(self):
        for closing in self:
            closing.state = "done"
            closing.amount = sum(closing.mapped("line_ids.amount_line"))

    def action_done(self):
        for closing in self:
            closing.state = "done"
            closing.amount = sum(closing.mapped("line_ids.amount_line"))
            query = """
                DELETE FROM
                    stock_close_period_line
                WHERE
                    close_id = %s
                    AND product_qty = 0
                    AND price_unit = 0;
            """ % closing.id
            self.env.cr.execute(query)
        return True

    def action_recompute_amount(self):
        for closing in self:
            closing.amount = sum(closing.mapped("line_ids.amount_line"))
