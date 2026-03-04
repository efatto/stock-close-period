# Copyright 2026 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.stock_close_period_evaluation_method.tests.test_stock_close_period_evaluation_method import (  # noqa: E501
    TestClosePeriodEvaluationMethod,
)


class TestClosePeriodExcludeCategory(TestClosePeriodEvaluationMethod):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_excluded = cls.env["product.product"].create(
            [
                {
                    "name": "Product Test Excluded by category",
                    "standard_price": 55.0,
                    "type": "product",
                    "categ_id": [
                        (
                            0,
                            0,
                            {
                                "name": "Excluded Category",
                                "exclude_from_stock_close_period": True,
                            },
                        )
                    ],
                    "seller_ids": [(6, 0, [cls.supplierinfo.id])],
                    "route_ids": [(6, 0, [cls.buy_route.id])],
                }
            ]
        )

    def test_00_stock_close_lifo(self):
        self._create_purchase_order_backdate(
            product_qty=10,
            price_unit=3,
            days_backdating=395,
            product=self.product_excluded,
        )
        self._create_purchase_order_backdate(
            product_qty=10, price_unit=7, days_backdating=365
        )
        stock_close_period_form = Form(
            self.env["stock.close.period"].with_user(self.test_user)
        )
        stock_close_period_form.force_evaluation_method = "standard"
        stock_close_period_form.name = "Stock close evaluation"
        stock_close_period_form.close_date = fields.Date.today() + timedelta(days=-300)
        stock_close_period = stock_close_period_form.save()
        stock_close_period.action_start()
        self.assertIn(self.product, stock_close_period.line_ids.mapped("product_id"))
        self.assertNotIn(
            self.product_excluded, stock_close_period.line_ids.mapped("product_id")
        )
