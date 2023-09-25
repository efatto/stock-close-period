# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    # related field to manage closed lines
    active = fields.Boolean(default=True)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # add field to manage closed lines
    active = fields.Boolean(related="move_id.active", store=True, default=True)
    company_id = fields.Many2one(related="move_id.company_id", store=True)

    def _get_last_closing(self, closing_id, product_id, company_id):
        # default value
        start_qty = 0
        start_price = 0

        if closing_id.last_closed_id:
            last_closed_id = closing_id.last_closed_id
        else:
            last_closed_id = self.env["stock.close.period"].search([
                ("state", "=", "done"),
                ("company_id", "=", company_id)
            ], order="close_date desc", limit=1)

        # search product
        closing_line_id = self.env["stock.close.period.line"].search([
            ("close_id", "=", last_closed_id.id),
            ("product_id", "=", product_id)
        ], limit=1)

        if closing_line_id:
            start_qty = closing_line_id.product_qty
            start_price = closing_line_id.price_unit

        return start_qty, start_price

    def _get_additional_landed_cost_new(self, move_id, company_id):
        svals = self.env["stock.valuation.adjustment.lines"].sudo().search([
            ("move_id", "=", move_id.id),
            ("cost_id.company_id", "=", company_id),
        ])
        if svals:
            additional_landed_cost_new = sum(svals.mapped("additional_landed_cost"))
        else:
            additional_landed_cost_new = 0
        return additional_landed_cost_new

    def _get_cost_stock_move_purchase_average(self, last_close_date, closing_line_id):
        product_id = closing_line_id.product_id
        company_id = closing_line_id.company_id.id

        # get all moves
        move_ids = self.env["stock.move"].search([
            ("state", "=", "done"),
            ("product_qty", ">", 0),
            ("product_id", "=", product_id.id),
            ("date", ">", last_close_date),
            ("active", ">=", 0),
            ("company_id", "=", company_id),
        ], order="date")

        # get start data from last close
        start_qty, start_price = self._get_last_closing(closing_line_id.close_id, product_id.id, company_id)
        if start_qty:
            inventory_amount = start_price * start_qty
            inventory_qty = start_qty
        else:
            inventory_amount = 0
            inventory_qty = 0

        cumulative_amount = 0
        cumulative_landed_cost = 0
        cumulative_qty = 0
        for move_id in move_ids.filtered(lambda m: m.purchase_line_id):
            if move_id.purchase_line_id.invoice_lines:
                cumulative_amount += sum(
                    abs(line.balance)
                    for line in move_id.purchase_line_id.invoice_lines
                )
                cumulative_qty += sum(move_id.purchase_line_id.invoice_lines.mapped("quantity"))
            elif move_id.purchase_line_id.currency_id == move_id.purchase_line_id.company_id.currency_id:
                price = move_id.purchase_line_id.price_unit
                cumulative_amount += move_id.purchase_line_id.product_uom_qty * price
                cumulative_qty += move_id.purchase_line_id.product_uom_qty
            else:
                price = move_id.purchase_line_id.currency_id._convert(
                    move_id.purchase_line_id.price_unit,
                    move_id.purchase_line_id.company_id.currency_id,
                    move_id.purchase_line_id.company_id,
                    move_id.date,
                    False
                )
                cumulative_amount += move_id.purchase_line_id.product_uom_qty * price
                cumulative_qty += move_id.purchase_line_id.product_uom_qty

            additional_landed_cost_new = self._get_additional_landed_cost_new(move_id, company_id)
            cumulative_landed_cost += additional_landed_cost_new

        if (cumulative_qty + inventory_qty) != 0:
            price_unit = (
                (inventory_amount + cumulative_amount + cumulative_landed_cost) / (cumulative_qty + inventory_qty)
            )
        else:
            price_unit = 0

        if price_unit == 0:
            closing_line_id.price_unit = product_id.standard_price
            closing_line_id.evaluation_method = "standard"
        else:
            closing_line_id.price_unit = price_unit
            closing_line_id.inventory_amount = inventory_amount
            closing_line_id.inventory_qty = inventory_qty
            closing_line_id.cumulative_amount = cumulative_amount
            closing_line_id.cumulative_landed_cost = cumulative_landed_cost
            closing_line_id.cumulative_qty = cumulative_qty
            closing_line_id.evaluation_method = "purchase"

    def _get_cost_stock_move_standard(self, closing_line_id):
        closing_line_id.price_unit = closing_line_id.product_id.standard_price
        closing_line_id.evaluation_method = "standard"

    def _check_consistency(self, closing_line_id):
        """
        Check inconsistency before elaborate closing line
        :return: True if line is consistency else False
        """
        return True

    def _search_same_product_value(self, closing_line_id):
        other_closing_line_id = self.env["stock.close.period.line"].search([
            ("close_id", "=", closing_line_id.close_id.id),
            ("product_id", "=", closing_line_id.product_id),
            ("price_unit", "!=", 0),
        ], limit=1)
        closing_line_id.price_unit = other_closing_line_id.price_unit
        closing_line_id.inventory_amount = other_closing_line_id.inventory_amount
        closing_line_id.inventory_qty = other_closing_line_id.inventory_qty
        closing_line_id.cumulative_amount = other_closing_line_id.cumulative_amount
        closing_line_id.cumulative_landed_cost = other_closing_line_id.cumulative_landed_cost
        closing_line_id.cumulative_qty = other_closing_line_id.cumulative_qty
        closing_line_id.evaluation_method = other_closing_line_id.evaluation_method

    def _recompute_cost_stock_move_purchase(self, closing_id):
        _logger.info("[1/2] Start recompute cost product purchase")
        company_id = closing_id.company_id.id

        # search only lines not elaborated
        closing_line_ids = self.env["stock.close.period.line"].search([
            ("close_id", "=", closing_id.id),
            ("evaluation_method", "not in", ["manual"]),
            ("price_unit", "=", 0)
        ])

        # get last close
        if closing_id.last_closed_id:
            last_closed_id = closing_id.last_closed_id
        else:
            last_closed_id = self.env["stock.close.period"].search([
                ("state", "=", "done"),
                ("company_id", "=", company_id)
            ], order="close_date desc", limit=1)

        # get last close date
        if last_closed_id:
            last_close_date = last_closed_id.close_date
        else:
            last_close_date = self.env["ir.config_parameter"].sudo().get_param("stock_close_period.last_close_date")

        # all closing line ready to elaborate
        elaborated_products = self.env["product.product"]
        for closing_line_id in closing_line_ids:
            if not self._check_consistency(closing_line_id):
                continue
            product_id = closing_line_id.product_id
            if product_id.id in elaborated_products.ids:
                self._search_same_product_value(closing_line_id)
            elaborated_products |= product_id

            if closing_id.force_evaluation_method != "no_force" and not closing_line_id.evaluation_method:
                if closing_id.force_evaluation_method == "purchase":
                    self._get_cost_stock_move_purchase_average(last_close_date, closing_line_id)
                if closing_id.force_evaluation_method == "standard":
                    self._get_cost_stock_move_standard(closing_line_id)
            else:
                if product_id.categ_id.property_cost_method in ["average", "fifo"]:
                    self._get_cost_stock_move_purchase_average(last_close_date, closing_line_id)
                if product_id.categ_id.property_cost_method == "standard":
                    self._get_cost_stock_move_standard(closing_line_id)

            self.env.cr.commit()
        _logger.info("[1/2] Finish recompute average cost product")

    def _write_results(self, closing_id):
        decimal = self.env["decimal.precision"].precision_get("Product Price")

        _logger.info("[2/2] Start writing results")

        # compute amount
        amount = 0
        for closing_line_id in closing_id.line_ids:
            row_value = closing_line_id.product_qty * closing_line_id.price_unit
            amount += round(row_value, decimal)

        # set amount closing
        closing_id.amount = amount

        _logger.info("[2/2] Finish writing results")

    def recompute_average_cost_period_purchase(self, closing_id):
        _logger.info("Recompute average cost period. Making in 2 phases:")
        _logger.info("[1/2] Recompute cost product purchase")
        _logger.info("[2/2] Write results")

        self._recompute_cost_stock_move_purchase(closing_id)
        self._write_results(closing_id)

        _logger.info("End recompute average cost product")
