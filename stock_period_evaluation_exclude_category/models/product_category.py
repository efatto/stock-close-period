from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    exclude_from_stock_period_evaluation = fields.Boolean(
        string="Exclude from Stock Close Period"
    )
