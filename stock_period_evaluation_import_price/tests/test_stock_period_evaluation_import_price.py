import base64
from io import BytesIO

from openpyxl import Workbook

from odoo import fields
from odoo.tests import TransactionCase


class TestStockPeriodEvaluationImportPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Import price product",
                "default_code": "IMP001",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.closing = cls.env["stock.close.period"].create(
            {
                "name": "Import price closing",
                "close_date": fields.Date.today(),
            }
        )
        cls.line = cls.env["stock.close.period.line"].create(
            {
                "close_id": cls.closing.id,
                "product_id": cls.product.id,
                "product_uom_id": cls.product.uom_id.id,
                "product_qty": 2.0,
                "price_unit": 10.0,
                "evaluation_method": "purchase",
            }
        )

    def test_00_import_prices(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Prodotto", "Costo unitario"])
        sheet.append(["IMP001", 12.5])
        sheet.append(["UNKNOWN", 99.0])
        content = BytesIO()
        workbook.save(content)
        workbook.close()
        self.closing.import_file = base64.b64encode(content.getvalue())
        self.closing.action_import_price_file()
        self.assertEqual(self.line.evaluation_method, "manual")
        self.assertAlmostEqual(self.line.price_unit, 12.5)
        self.assertFalse(self.line.evaluation_details)
        self.assertAlmostEqual(self.closing.amount, 25.0)
