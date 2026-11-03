import base64
from io import BytesIO
from zipfile import BadZipFile

import openpyxl
import xlrd
from openpyxl.utils.exceptions import InvalidFileException

from odoo import fields, models


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    import_file = fields.Binary(string="Import File with prices", copy=False)
    import_file_name = fields.Char(copy=False)

    @staticmethod
    def _get_import_rows(decoded_data):
        try:
            workbook = openpyxl.load_workbook(
                filename=BytesIO(decoded_data), data_only=True, read_only=True
            )
            try:
                sheet = workbook.worksheets[0]
                return [list(row) for row in sheet.iter_rows(values_only=True)]
            finally:
                workbook.close()
        except (InvalidFileException, BadZipFile):
            # Fallback for legacy .xls files.
            workbook = xlrd.open_workbook(file_contents=decoded_data)
            sheet = workbook.sheet_by_index(0)
            return [
                [sheet.cell_value(row, col) for col in range(sheet.ncols)]
                for row in range(sheet.nrows)
            ]

    def action_import_price_file(self):
        self.ensure_one()
        decoded_data = base64.decodebytes(self.import_file)
        rows = self._get_import_rows(decoded_data)
        if not rows:
            return
        header_row = rows[0]
        for row in rows[1:]:
            price_unit = 0
            price_unit_found = False
            product_default_code = False
            for cx, value in enumerate(row):
                header = (
                    str(header_row[cx] or "").lower() if cx < len(header_row) else ""
                )
                if any(x in header for x in ["costo", "prezzo", "unit"]):
                    price_unit_found = True
                    price_unit = value or 0
                if "prodotto" in header:
                    product_default_code = str(value) if value else False
                if product_default_code and price_unit_found:
                    lines = self.line_ids.filtered(
                        lambda li, pdc=product_default_code: li.product_id.default_code
                        == pdc
                    )
                    if lines:
                        lines.write(
                            {
                                "evaluation_method": "manual",
                                "price_unit": price_unit,
                                "evaluation_details": "",
                            }
                        )
                    price_unit = 0
                    product_default_code = False
        self.action_recompute_amount()
