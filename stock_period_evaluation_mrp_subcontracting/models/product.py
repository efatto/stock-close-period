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
        # e.g. Prodotto padre con componenti e subcomponenti
        # descrizione                           prezzo unit	q.tà	prezzo totale
        # COXABCH00002	                        3,54041	    0,53	1,87641
        # SUBFORNITORE			                                    2,92
        # ORD30562	                            0,01498	    2	    0,02996
        # TEMPO	                                23	        0,00556	0,12777
        # Totale			                                        4,95414
        self.ensure_one()
        total = super()._get_extra_cost(bom)
        if bom.type == "subcontract" and any(
            seller.is_subcontractor for seller in self.seller_ids
        ):
            total += self._get_cost()
        return total
