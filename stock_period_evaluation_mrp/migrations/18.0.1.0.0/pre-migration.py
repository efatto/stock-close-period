# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

# The module is renamed from stock_close_period_mrp in apriori.py, so the old
# XML-IDs are already stored under the new module name when this script is
# executed.
MODULE = "stock_period_evaluation_mrp"

XMLID_RENAMES = [
    ("stock_close_period_line_tree", "stock_period_evaluation_line_tree"),
    ("stock_close_period_tree_inherit", "stock_period_evaluation_tree_inherit"),
    ("stock_close_period_form_inherit", "stock_period_evaluation_form_inherit"),
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
