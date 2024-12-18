from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_cost(self):
        # overridable method to customize cost used for evaluation
        super()._get_cost()
        return self.direct_cost
