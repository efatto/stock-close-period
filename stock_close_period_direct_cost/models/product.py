from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_cost(self):
        # overridable method to customize cost used for evaluation
        super()._get_cost()
        cost = self.direct_cost
        if not cost:
            cost = self.standard_price - self.testing_cost
            # if there is a seller which has 0 as price but a depreciation cost,
            # subctract it
            if self.seller_ids:
                cost -= self.seller_ids[0].depreciation_cost
        return cost
