# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Close Period Extra Evaluation Methods",
    "summary": "Add FIFO and LIFO to evaluation methods",
    "version": "14.0.1.0.0",
    "category": "Stock",
    "author": "Sergio Corato",
    "website": "https://github.com/sergiocorato/stock-close-period",
    "license": "AGPL-3",
    "depends": [
        "purchase_stock",  # for tests
        "sale_stock",  # for tests
        "stock_close_period",
        "stock_move_backdating",  # for tests
    ],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
