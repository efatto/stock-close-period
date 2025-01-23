from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_bom_price(self, bom, boms_to_recompute=False):
        self.ensure_one()
        total = super()._compute_bom_price(bom, boms_to_recompute)
        if bom.type == "subcontract" and any(
            seller.is_subcontractor for seller in self.seller_ids
        ):
            total += self._get_cost()
        return total

    def _get_extra_cost(self, bom):
        self.ensure_one()
        total = super()._get_extra_cost(bom)
        if bom.type == "subcontract" and any(
            seller.is_subcontractor for seller in self.seller_ids
        ):
            total += self._get_cost()
        return total
