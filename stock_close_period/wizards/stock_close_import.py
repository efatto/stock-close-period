# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import unicodecsv

from datetime import *

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class StockCloseImportWizard(models.TransientModel):
    _name = "stock.close.import.wizard"
    _description = "Stock Close Import Wizard"

    file = fields.Binary()
    close_id = fields.Many2one("stock.close.period", string="Stock Close Period")

    def load_products(self, lines):
        products = {}
        for index, row in enumerate(lines):
            default_code = row["CODE"]
            product_obj = self.env["product.product"].search([
                ("default_code", "=", default_code),
            ], limit=1)
            if not product_obj:
                raise UserError(_("Product %s not found") % default_code)
            products[default_code] = product_obj[0]
        return products

    def import_csv(self):
        # set done close_id
        self.close_id.work_start = datetime.now()

        try:
            file_to_import = base64.decodebytes(self.file).splitlines()
            reader = unicodecsv.reader(file_to_import, encoding="utf-8", delimiter=";")
            lines = []
            headers = False

            for index, row in enumerate(reader):
                headers = row
                break

            parsed_data_lines = unicodecsv.DictReader(
                file_to_import,
                fieldnames=headers,
                encoding="utf-8",
                delimiter=";"
            )

            for index, row in enumerate(parsed_data_lines):
                if index == 0:
                    continue
                lines.append({
                    "CODE": str(row["CODE"]),
                    "COST": str(row["COST"]).replace(",", "."),
                    "QTY": str(row["QTY"]).replace(",", "."),
                })
            products = self.load_products(lines)
            total = 0.0
            dp_qty = 4
            dp_price = 5
            for index, row in enumerate(lines):
                product_id = products[row["CODE"]].id
                unit_cost = round(float(row["COST"]), dp_price)
                qty = round(float(row["QTY"]), dp_qty)
                total += unit_cost * qty
                self.env["stock.close.period.line"].with_context(tracking_disable=True).create({
                    "close_id": self.close_id.id,
                    "product_id": product_id,
                    "price_unit": unit_cost,
                    "product_qty": qty,
                    "product_uom_id": products[row["CODE"]].product_tmpl_id.uom_id.id,
                    "evaluation_method": "",
                })

            # set done close_id
            self.close_id.amount = total
            self.close_id.work_end = datetime.now()
            self.close_id.state = "done"

        except Exception as e:
            raise UserError(e)
