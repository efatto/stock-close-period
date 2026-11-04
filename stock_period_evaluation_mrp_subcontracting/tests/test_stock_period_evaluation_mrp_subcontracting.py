from odoo import Command
from odoo.tests import TransactionCase


class TestStockPeriodEvaluationMrpSubcontracting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.subcontractor = cls.env["res.partner"].create({"name": "Subcontractor"})
        cls.component = cls.env["product.product"].create(
            {
                "name": "Subcontract component",
                "type": "consu",
                "is_storable": True,
                "standard_price": 5.0,
            }
        )
        cls.finished = cls.env["product.product"].create(
            {
                "name": "Subcontracted product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "subcontract",
                "subcontractor_ids": [Command.set([cls.subcontractor.id])],
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
        cls.supplierinfo = cls.env["product.supplierinfo"].create(
            {
                "partner_id": cls.subcontractor.id,
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "price": 10.0,
                "min_qty": 0.0,
            }
        )

    def test_00_subcontracting_cost(self):
        # The subcontractor cost is added once by the core mrp_subcontracting_account
        # bridge module, through the standard BOM price computation.
        self.assertTrue(self.supplierinfo.is_subcontractor)
        self.assertAlmostEqual(self.finished._compute_bom_price(self.bom), 20.0)
        # The closing evaluation adds the direct cost only through _get_extra_cost.
        self.assertAlmostEqual(self.finished._get_extra_cost(self.bom), 10.0)
