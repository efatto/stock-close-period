# Copyright 2026 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields
from odoo.tests import TransactionCase


class TestClosePeriodExcludeCategory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.excluded_category = cls.env["product.category"].create(
            {
                "name": "Excluded Category",
                "exclude_from_stock_close_period": True,
            }
        )
        cls.included_category = cls.env["product.category"].create(
            {"name": "Included Category"}
        )
        cls.child_category = cls.env["product.category"].create(
            {
                "name": "Child of Excluded Category",
                "parent_id": cls.excluded_category.id,
            }
        )
        cls.product_included = cls.env["product.product"].create(
            {
                "name": "Product Test Included",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.included_category.id,
            }
        )
        cls.product_child = cls.env["product.product"].create(
            {
                "name": "Product Test Child Category",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.child_category.id,
            }
        )
        cls.product_excluded = cls.env["product.product"].create(
            {
                "name": "Product Test Excluded by category",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.excluded_category.id,
            }
        )

    def _create_closing(self):
        closing = self.env["stock.close.period"].create(
            {
                "name": "Stock close evaluation",
                "close_date": fields.Date.today(),
            }
        )
        closing.action_start()
        return closing

    def test_00_exclude_category(self):
        closing = self._create_closing()
        product_ids = closing.line_ids.mapped("product_id")
        self.assertIn(self.product_included, product_ids)
        # Only the selected category is excluded, its children are not.
        self.assertIn(self.product_child, product_ids)
        self.assertNotIn(self.product_excluded, product_ids)

    def test_01_include_category(self):
        self.excluded_category.exclude_from_stock_close_period = False
        closing = self._create_closing()
        self.assertIn(self.product_excluded, closing.line_ids.mapped("product_id"))
