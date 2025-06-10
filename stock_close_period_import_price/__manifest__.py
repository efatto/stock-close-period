# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Close Period Import Prices",
    "summary": "Add ability to import prices on a stock close period",
    "version": "14.0.1.0.1",
    "category": "Stock",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/stock-close-period",
    "license": "AGPL-3",
    "depends": [
        "stock_close_period_evaluation_method",
    ],
    "data": [
        "views/stock_close_views.xml",
    ],
    "installable": True,
    "application": False,
}
