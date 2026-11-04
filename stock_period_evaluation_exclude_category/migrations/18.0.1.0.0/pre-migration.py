# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.tools.sql import column_exists

FIELD_RENAMES = [
    (
        "product.category",
        "product_category",
        "exclude_from_stock_close_period",
        "exclude_from_stock_period_evaluation",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    for model, table, old_field, new_field in FIELD_RENAMES:
        if column_exists(env.cr, table, old_field) and not column_exists(
            env.cr, table, new_field
        ):
            openupgrade.rename_fields(env, [(model, table, old_field, new_field)])
