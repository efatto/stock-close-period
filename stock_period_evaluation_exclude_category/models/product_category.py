from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    exclude_from_stock_close_period = fields.Boolean(
        string="Exclude from Stock Close Period"
    )
