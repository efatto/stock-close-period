# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Close Period Landed Costs",
    "summary": "Glue module with Stock Close Period and Stock Landed Costs",
    "version": "14.0.1.0.0",
    "category": "Stock",
    "author": "Pordenone Linux User Group (PNLUG), Odoo Community Association (OCA),"
    "DinamicheAziendali",
    "website": "https://github.com/DinamicheAziendali/stock_close_period",
    "license": "AGPL-3",
    "depends": [
        "stock_close_period",
        "l10n_it_intrastat_tariff",
        "res_country_logistic_charge",
        "res_currency_change_charge",
    ],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
