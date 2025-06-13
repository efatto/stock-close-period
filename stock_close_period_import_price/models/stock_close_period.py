import base64

import xlrd

from odoo import fields, models


class StockClosePeriod(models.Model):
    _inherit = "stock.close.period"

    import_file = fields.Binary(string="Import File with prices")
    import_file_name = fields.Char(string="Import File Name")

    def action_import_price_file(self):
        self.ensure_one()
        decoded_data = base64.decodebytes(self.import_file)
        wb = xlrd.open_workbook(file_contents=decoded_data)
        st = wb.sheet_by_index(0)
        header_row = st.row(0)
        for rx in range(1, st.nrows):
            price_unit = 0
            product_default_code = False
            for cx, c in enumerate(st.row(rx)):
                if header_row[cx].value == "Costo unitario":
                    price_unit = c.value or 0
                if header_row[cx].value == "Prodotto":
                    product_default_code = c.value
                if product_default_code:
                    lines = self.line_ids.filtered(
                        lambda l: l.product_id.default_code == product_default_code
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
