# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Close Period - MRP",
    "summary": "Stock Close Period - MRP",
    "version": "18.0.1.0.0",
    "category": "Stock",
    "author": "Pordenone Linux User Group (PNLUG), DinamicheAziendali, Sergio Corato",
    "website": "https://github.com/efatto/stock-close-period",
    "license": "AGPL-3",
    "depends": [
        "mrp",
        "mrp_account",
        "stock_period_evaluation",
        "stock_period_evaluation_method",
    ],
    "data": [
        "views/stock_close_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}
