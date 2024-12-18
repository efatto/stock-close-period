# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.stock_move_backdating.tests.common import TestCommon


class TestPicking(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env.ref("base.res_partner_2")
        cls.customer.customer_rank = 1
        cls.buy_route = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.vendor = cls.env.ref("base.res_partner_3")
        supplierinfo = cls.env["product.supplierinfo"].create(
            [
                {
                    "name": cls.vendor.id,
                    "delay": 10,
                }
            ]
        )
        cls.product = cls.env["product.product"].create(
            [
                {
                    "name": "Product Test",
                    "standard_price": 55.0,
                    "direct_cost": 50.0,
                    "type": "product",
                    "seller_ids": [(6, 0, [supplierinfo.id])],
                    "route_ids": [(6, 0, [cls.buy_route.id])],
                }
            ]
        )
        # Create User:
        cls.test_user = cls.env["res.users"].create(
            {
                "name": "John",
                "login": "test",
                "email": "test@test.email",
            }
        )
        cls.test_user.write(
            {
                "groups_id": [
                    (4, cls.env.ref("sales_team.group_sale_salesman").id),
                    (4, cls.env.ref("purchase.group_purchase_user").id),
                ],
            }
        )

    def _create_purchase_order_backdate(self, product_qty, price_unit, days_backdating):
        date_backdating = self._get_datetime_backdating(days_backdating)
        purchase_order_form = Form(self.env["purchase.order"].with_user(self.test_user))
        purchase_order_form.partner_id = self.vendor
        with purchase_order_form.order_line.new() as order_line:
            order_line.product_id = self.product
            order_line.product_qty = product_qty
            order_line.price_unit = price_unit
        purchase_order = purchase_order_form.save()
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created"
        )
        self.assertEqual(len(purchase_order.picking_ids), 1)
        picking = purchase_order.picking_ids
        self.picking = picking
        self._transfer_picking_with_dates(date_backdating)

    def _create_sale_order_backdate(self, product_qty, days_backdating):
        date_backdating = self._get_datetime_backdating(days_backdating)
        sale_order_form = Form(self.env["sale.order"].with_user(self.test_user))
        sale_order_form.partner_id = self.customer
        with sale_order_form.order_line.new() as order_line:
            order_line.product_id = self.product
            order_line.product_uom_qty = product_qty
            order_line.price_unit = 100
        sale_order = sale_order_form.save()
        sale_order.action_confirm()
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created"
        )
        self.assertEqual(len(sale_order.picking_ids), 1)
        picking = sale_order.picking_ids
        self.picking = picking
        self._transfer_picking_with_dates(date_backdating)

    def _refresh_close_period(self, stock_close_period):
        stock_close_period.action_cancel()
        stock_close_period.action_set_to_draft()
        stock_close_period.action_start()
        stock_close_line = stock_close_period.line_ids.filtered(
            lambda x: x.product_id == self.product
        )
        return stock_close_line

    def test_00_stock_close_lifo(self):
        self._create_purchase_order_backdate(
            product_qty=10, price_unit=5, days_backdating=365
        )
        self._create_purchase_order_backdate(
            product_qty=10, price_unit=5, days_backdating=365
        )

        stock_close_period_form = Form(
            self.env["stock.close.period"].with_user(self.test_user)
        )
        stock_close_period_form.force_evaluation_method = "lifo"
        stock_close_period_form.name = "Stock close evaluation"
        stock_close_period_form.close_date = fields.Date.today() + timedelta(days=-300)
        stock_close_period = stock_close_period_form.save()
        stock_close_period.action_start()
        self.assertTrue(stock_close_period.line_ids)
        stock_close_line = stock_close_period.line_ids.filtered(
            lambda x: x.product_id == self.product
        )
        self.assertEqual(stock_close_line.product_qty, 20)
        stock_close_period.action_recalculate_purchase()
        self.assertEqual(stock_close_line.price_unit, 5)
        stock_close_period.action_done()
        self.assertEqual(stock_close_period.state, "done")

        self._create_purchase_order_backdate(
            product_qty=10, price_unit=7, days_backdating=100
        )

        self._create_purchase_order_backdate(
            product_qty=10, price_unit=10, days_backdating=90
        )

        stock_close_period_form1 = Form(
            self.env["stock.close.period"].with_user(self.test_user)
        )
        stock_close_period_form1.force_evaluation_method = "lifo"
        stock_close_period_form1.name = "Stock close evaluation 1"
        stock_close_period_form1.close_date = fields.Date.today()
        stock_close_period_form1.last_closed_id = stock_close_period
        stock_close_period1 = stock_close_period_form1.save()
        stock_close_period1.action_start()
        self.assertTrue(stock_close_period1.line_ids)
        stock_close_line1 = stock_close_period1.line_ids.filtered(
            lambda x: x.product_id == self.product
        )

        self.assertEqual(stock_close_line1.product_qty, 40)
        stock_close_period1.action_recalculate_purchase()
        self.assertEqual(stock_close_line1.price_unit, 6.75)

        self._create_sale_order_backdate(product_qty=30, days_backdating=80)
        stock_close_line1 = self._refresh_close_period(stock_close_period1)
        self.assertEqual(stock_close_line1.product_qty, 10)
        stock_close_period1.action_recalculate_purchase()
        self.assertAlmostEqual(stock_close_line1.price_unit, 5)

        self._create_purchase_order_backdate(
            product_qty=15, price_unit=12, days_backdating=70
        )
        stock_close_line1 = self._refresh_close_period(stock_close_period1)
        self.assertEqual(stock_close_line1.product_qty, 25)
        stock_close_period1.action_recalculate_purchase()
        self.assertAlmostEqual(stock_close_line1.price_unit, 9.2)

        self._create_sale_order_backdate(product_qty=5, days_backdating=60)
        stock_close_line1 = self._refresh_close_period(stock_close_period1)
        self.assertEqual(stock_close_line1.product_qty, 20)
        stock_close_period1.action_recalculate_purchase()
        self.assertAlmostEqual(stock_close_line1.price_unit, 8.5)

        self._create_purchase_order_backdate(
            product_qty=10, price_unit=15, days_backdating=50
        )
        stock_close_line1 = self._refresh_close_period(stock_close_period1)
        self.assertEqual(stock_close_line1.product_qty, 30)
        stock_close_period1.action_recalculate_purchase()
        self.assertAlmostEqual(stock_close_line1.price_unit, 10.67)
