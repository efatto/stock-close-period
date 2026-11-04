# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

# The module is renamed from stock_close_period_evaluation_method in apriori.py,
# so the old XML-IDs are already stored under the new module name when this
# script is executed.
MODULE = "stock_period_evaluation_method"

XMLID_RENAMES = [
    ("stock_close_period_form", "stock_period_evaluation_form"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(
        env.cr,
        [
            (f"{MODULE}.{old_name}", f"{MODULE}.{new_name}")
            for old_name, new_name in XMLID_RENAMES
        ],
    )
