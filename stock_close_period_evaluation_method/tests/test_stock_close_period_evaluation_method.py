# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import Form

from odoo.addons.stock_move_backdating.tests.common import TestCommon


class TestPicking(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.partner.customer_rank = 1
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
                    "standard_price": 50.0,
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

    def test_00_purchase_order(self):
        purchase_order_form = Form(self.env["purchase.order"].with_user(self.test_user))
        purchase_order_form.partner_id = self.vendor
        with purchase_order_form.order_line.new() as order_line:
            order_line.product_id = self.product
            order_line.product_qty = 10
            order_line.price_unit = 5
        purchase_order = purchase_order_form.save()
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created"
        )
        date_backdating = self._get_datetime_backdating(365)
        self.assertEqual(len(purchase_order.picking_ids), 1)
        picking = purchase_order.picking_ids
        self.picking = picking
        self._transfer_picking_with_dates(date_backdating)
