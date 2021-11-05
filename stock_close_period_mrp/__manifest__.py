# Copyright 2020 Marcelo Frare (Associazione PNLUG - Gruppo Odoo)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Close Period - MRP",
    "summary": "Stock Close Period - MRP",
    "version": "12.0.1.0.0",
    "category": "Stock",
    "author": "Pordenone Linux User Group (PNLUG), Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "license": "AGPL-3",
    "depends": [
        "stock_close_period",
        "mrp",
        "mrp_bom_cost",
    ],
    "data": [
        "views/stock_close_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
