# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "ITA - Stock close period report",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/stock-close-period",
    "license": "AGPL-3",
    "depends": [
        "report_xlsx",
        "stock_period_evaluation",
    ],
    "data": [
        "reports/layout.xml",
        "reports/stock_period_evaluation_report.xml",
        "reports/xlsx_stock_close_product.xml",
    ],
    "installable": True,
}
