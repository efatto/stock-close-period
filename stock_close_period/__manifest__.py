# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Close Period",
    "summary": "Stock Close Period",
    "version": "16.0.1.0.0",
    "category": "Stock",
    "author": "Pordenone Linux User Group (PNLUG), Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "purchase_stock",
        "stock_account",
        "report_xlsx",
    ],
    "data": [
        "security/stock_close_group.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "views/stock_close_views.xml",
        "wizards/stock_close_import.xml",
        "wizards/stock_close_print.xml",
        "reports/xlsx_stock_close_print.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
