from datetime import timedelta
from io import BytesIO

import xlsxwriter

from odoo import fields
from odoo.tests import TransactionCase


class TestStockPeriodEvaluationReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("it_IT")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Report product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.previous_closing = cls.env["stock.close.period"].create(
            {
                "name": "Previous closing",
                "close_date": fields.Date.today() - timedelta(days=2),
            }
        )
        cls.closing = cls.env["stock.close.period"].create(
            {
                "name": "Report closing",
                "close_date": fields.Date.today() + timedelta(days=1),
                "last_closed_id": cls.previous_closing.id,
            }
        )
        cls.closing_line = cls.env["stock.close.period.line"].create(
            {
                "close_id": cls.closing.id,
                "product_id": cls.product.id,
                "product_uom_id": cls.product.uom_id.id,
                "location_id": cls.stock_location.id,
                "product_qty": 10.0,
                "price_unit": 10.0,
                "inventory_qty": 0.0,
                "inventory_amount": 0.0,
            }
        )
        cls.stock_move = cls.env["stock.move"].create(
            {
                "name": "Incoming report move",
                "product_id": cls.product.id,
                "product_uom_qty": 10.0,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.supplier_location.id,
                "location_dest_id": cls.stock_location.id,
            }
        )
        cls.stock_move._action_confirm()
        cls.stock_move._action_assign()
        cls.stock_move.picked = True
        cls.stock_move._action_done()
        cls.stock_move.date = cls.stock_move.move_line_ids.date = fields.Datetime.now()

    def test_00_report_action(self):
        report = self.env.ref("stock_period_evaluation_report.xlsx_stock_close_product")
        self.assertEqual(report.model, "stock.close.period")
        self.assertEqual(report.binding_model_id.model, "stock.close.period")

    def test_01_xlsx_report(self):
        self.assertEqual(self.stock_move.state, "done")
        report_model = self.env[
            "report.stock_period_evaluation_report.xlsx_stock_close_product"
        ].with_context(active_id=self.closing.id)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        report_model.generate_xlsx_report(workbook, {}, self.closing)
        workbook.close()
        self.assertTrue(output.getvalue())

    def test_02_pdf_move_lines(self):
        report_model = self.env[
            "report.stock_period_evaluation_report.report_product_print"
        ]
        move_lines = report_model._get_move_lines(self.closing_line)
        self.assertIn(self.stock_move.move_line_ids, move_lines)

    def test_03_pdf_template(self):
        report_model = self.env[
            "report.stock_period_evaluation_report.report_product_print"
        ]
        html = self.env["ir.qweb"]._render(
            "stock_period_evaluation_report.report_product_print",
            {
                "docs": self.closing,
                "get_move_lines": report_model._get_move_lines,
                "res_company": self.env.company,
                "title": "Stock report",
                "lang": self.env.user.lang,
                "data_report_margin_top": 10,
                "data_report_header_spacing": 10,
                "data_report_dpi": 90,
                "data_report_landscape": True,
                "web_base_url": "http://localhost",
                "full_width": False,
            },
        )
        self.assertIn("Report closing", str(html))
