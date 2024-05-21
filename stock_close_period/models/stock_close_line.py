# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class StockClosePeriodLine(models.Model):
    _name = "stock.close.period.line"
    _description = "Stock Close Period Line"
    _rec_name = "product_id"

    close_id = fields.Many2one(
        "stock.close.period",
        string="Stock Close Period",
        index=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain=[("type", "=", "product")],
        index=True,
        required=True,
    )
    product_name = fields.Char(related="product_id.name", store=True, readonly=True)
    product_code = fields.Char(
        related="product_id.default_code", store=True, readonly=True
    )
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="UOM",
        required=True,
        default=lambda self: self.env.ref(
            "uom.product_uom_unit", raise_if_not_found=True
        ),
    )
    categ_name = fields.Char(
        string="Category Name",
        related="product_id.categ_id.complete_name",
        store=True,
        readonly=True,
    )
    evaluation_method = fields.Selection(
        [("purchase", "Purchase"), ("standard", "Standard"), ("manual", "Manual")],
        copy=False,
    )
    product_qty = fields.Float(
        string="End Quantity", digits="Product Unit of Measure", default=0
    )
    price_unit = fields.Float(string="End Average Price", digits="Product Price")
    inventory_amount = fields.Float(string="Inventory Amount", digits="Product Price")
    inventory_qty = fields.Float(
        string="Inventory Quantity", digits="Product Unit of Measure"
    )
    cumulative_amount = fields.Float(string="Cumulative Amount", digits="Product Price")
    cumulative_landed_cost = fields.Float(
        string="Cumulative Landed Cost", digits="Product Price"
    )
    cumulative_qty = fields.Float(
        string="Cumulative Quantity", digits="Product Unit of Measure"
    )
    amount_line = fields.Float(compute="_compute_amount_line", digits="Product Price")
    location_id = fields.Many2one("stock.location", string="Location")
    lot_id = fields.Many2one("stock.production.lot", string="Lot/Serial Number")
    owner_id = fields.Many2one("res.partner", string="Owner")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.depends("close_id.company_id")
    def _compute_company(self):
        for line in self:
            line.company_id = line.close_id.company_id.id

    @api.depends("product_qty", "price_unit")
    def _compute_amount_line(self):
        for line in self:
            line.amount_line = line.product_qty * line.price_unit
