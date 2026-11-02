from odoo import Command, fields
from odoo.tests import TransactionCase


class TestStockPeriodEvaluationMrp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.component = cls.env["product.product"].create(
            {
                "name": "MRP component",
                "type": "consu",
                "is_storable": True,
                "standard_price": 10.0,
            }
        )
        cls.finished = cls.env["product.product"].create(
            {
                "name": "MRP finished product",
                "type": "consu",
                "is_storable": True,
                "standard_price": 100.0,
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.component.id,
                            "product_qty": 2.0,
                            "product_uom_id": cls.component.uom_id.id,
                        }
                    )
                ],
            }
        )
        cls.workcenter = cls.env["mrp.workcenter"].create(
            {
                "name": "MRP workcenter",
                "costs_hour": 60.0,
            }
        )
        cls.env["mrp.routing.workcenter"].create(
            {
                "name": "MRP operation",
                "bom_id": cls.bom.id,
                "workcenter_id": cls.workcenter.id,
                "time_mode": "manual",
                "time_cycle_manual": 30.0,
            }
        )

    def _create_closing(self, force_standard_price=False):
        closing = self.env["stock.close.period"].create(
            {
                "name": "MRP closing",
                "close_date": fields.Date.today(),
                "force_standard_price": force_standard_price,
            }
        )
        self.env["stock.close.period.line"].create(
            {
                "close_id": closing.id,
                "product_id": self.component.id,
                "product_uom_id": self.component.uom_id.id,
                "product_qty": 10.0,
                "price_unit": 10.0,
                "evaluation_method": "purchase",
            }
        )
        finished_line = self.env["stock.close.period.line"].create(
            {
                "close_id": closing.id,
                "product_id": self.finished.id,
                "product_uom_id": self.finished.uom_id.id,
                "product_qty": 2.0,
                "price_unit": 0.0,
            }
        )
        return closing, finished_line

    def test_00_recalculate_production(self):
        closing, finished_line = self._create_closing()
        closing.action_recalculate_production()
        self.assertAlmostEqual(finished_line.price_unit, 50.0)
        self.assertEqual(finished_line.evaluation_method, "production")
        self.assertTrue(closing.production_ok)
        self.assertTrue(closing.work_end_date)
        self.assertIn("BOM unit cost", finished_line.evaluation_details)

    def test_01_force_standard_price(self):
        closing, finished_line = self._create_closing(force_standard_price=True)
        closing.action_recalculate_production()
        self.assertAlmostEqual(finished_line.price_unit, self.finished.standard_price)
        self.assertEqual(finished_line.evaluation_method, "standard")

    def test_02_recalculate_line_production(self):
        closing, finished_line = self._create_closing()
        finished_line.action_recalculate_production()
        self.assertAlmostEqual(finished_line.price_unit, 50.0)
        self.assertEqual(finished_line.evaluation_method, "production")
        self.assertTrue(closing.work_end_date)
