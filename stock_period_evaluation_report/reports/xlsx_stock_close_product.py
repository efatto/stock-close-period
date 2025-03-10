from xlsxwriter.utility import xl_rowcol_to_cell

from odoo import _, models


class XlsxStockClosePeriodProduct(models.AbstractModel):
    _name = "report.stock_close_period_report.xlsx_stock_close_product"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report Stock Close Product XLSX"

    def generate_xlsx_report(self, workbook, data, lines):
        stock_close_period = self.env["stock.close.period"].browse(
            self.env.context.get("active_id")
        )
        lines = stock_close_period.line_ids

        sheet = workbook.add_worksheet(_("Stock Close Period Product"))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)

        border_style = workbook.add_format({"border": 1})
        title_style = workbook.add_format(
            {"bold": False, "bg_color": "#C0C0C0", "border": 1}
        )
        qty_format = workbook.add_format({"num_format": "#,##0.00", "border": 1})
        qty_format_title = workbook.add_format(
            {
                "num_format": "#,##0.00",
                "bold": False,
                "bg_color": "#C0C0C0",
                "border": 1,
            }
        )
        currency_format = workbook.add_format({"num_format": "€ #,##0.00", "border": 1})
        currency_format_title = workbook.add_format(
            {
                "num_format": "€ #,##0.00",
                "bold": False,
                "bg_color": "#C0C0C0",
                "border": 1,
            }
        )
        date_format = workbook.add_format({"num_format": "DD-MM-YYYY", "border": 1})

        # header
        sheet_title = [
            _("Date"),
            _("Transfer type"),
            _("Origin"),
            _("Destination"),
            _("Purchase Amount"),
            _("UoM"),
            _("Quantity IN"),
            _("Quantity OUT"),
            _("Final Quantity"),
        ]
        i = 0
        sheet.write_row(i, 0, sheet_title, title_style)
        sheet.freeze_panes(1, 0)
        i = 1
        in_qty = 0.0
        out_qty = 0.0
        evaluation_amount = 0.0
        # rows
        for row in lines:
            row_in_qty = 0.0
            row_out_qty = 0.0
            evaluation_amount += row.inventory_amount
            sheet.write(i, 0, _("Description:"), title_style)
            sheet.merge_range(
                i,
                1,
                i,
                8,
                row.product_id.with_context({"lang": "it_IT"}).name or "",
                title_style,
            )
            i += 1
            sheet.write(i, 0, _("Product Code:"), title_style)
            sheet.write(i, 1, row.product_code or "", title_style)
            sheet.write(i, 2, _("Initial Value:"), title_style)
            sheet.write(i, 3, row.inventory_amount or "", currency_format_title)
            sheet.write(i, 4, _("Final Value:"), title_style)
            sheet.write(i, 5, row.amount_line or "", currency_format_title)
            i += 1
            sheet.write(i, 0, _("Evaluation method:"), title_style)
            sheet.write(i, 1, row.evaluation_method or "", title_style)
            sheet.write(i, 2, _("Initial Quantity:"), title_style)
            sheet.write(i, 3, row.inventory_qty or "", qty_format_title)
            sheet.write(i, 4, _("Final Quantity:"), title_style)
            sheet.write(i, 5, row.product_qty or "", qty_format_title)
            i += 1
            moves = self.env["stock.move"].search(
                [
                    ("state", "=", "done"),
                    ("product_qty", ">", 0),
                    ("product_id", "=", row.product_id.id),
                    ("date", ">", row.close_id.last_close_date),
                    ("date", "<=", row.close_id.close_date),
                    ("company_id", "=", row.close_id.company_id.id),
                ],
            )
            moves = sorted(
                [x for x in moves],
                key=lambda m: (
                    m.date.strftime("%Y-%m-%d"),
                    "a"
                    if m.location_id.usage != "internal"
                    and m.location_dest_id.usage == "internal"
                    else "z",
                ),
            )
            i_row = i
            for move in moves:
                move_type = (
                    "in"
                    if (
                        move.location_id.usage != "internal"
                        and move.location_dest_id.usage == "internal"
                    )
                    else "out"
                )
                sheet.write(i, 0, move.date, date_format)
                sheet.write(i, 1, move_type.upper(), border_style)
                sheet.write(i, 2, move.location_id.name, border_style)
                sheet.write(i, 3, move.location_dest_id.name, border_style)
                sheet.write(
                    i, 4, move.purchase_line_id.price_subtotal or 0.0, currency_format
                )
                sheet.write(i, 5, move.product_uom.name, border_style)
                if move_type == "in":
                    row_in_qty += move.quantity_done
                    sheet.write(i, 6, move.quantity_done or 0.0, qty_format)
                    sheet.write(i, 7, 0.0, qty_format)
                if move_type == "out":
                    row_out_qty += move.quantity_done
                    sheet.write(i, 6, 0.0, qty_format)
                    sheet.write(i, 7, move.quantity_done or 0.0, qty_format)
                sheet.write(i, 8, row_in_qty - row_out_qty, qty_format)
                i += 1
            in_qty += row_in_qty
            out_qty += row_out_qty
            sheet.write(i, 0, _("Totals"), title_style)
            sheet.write(i, 1, row.product_code, title_style)
            sheet.merge_range(
                i,
                2,
                i,
                5,
                row.product_id.with_context({"lang": "it_IT"}).name or "",
                title_style,
            )
            sheet.write_formula(
                i,
                6,
                "=SUM(%s:%s)"
                % (
                    xl_rowcol_to_cell(i_row, 6),
                    xl_rowcol_to_cell(i - 1, 6),
                ),
                qty_format_title,
                "",
            )
            sheet.write_formula(
                i,
                7,
                "=SUM(%s:%s)"
                % (
                    xl_rowcol_to_cell(i_row, 7),
                    xl_rowcol_to_cell(i - 1, 7),
                ),
                qty_format_title,
                "",
            )
            sheet.write_formula(
                i,
                8,
                "=%s-%s"
                % (
                    xl_rowcol_to_cell(i, 6),
                    xl_rowcol_to_cell(i, 7),
                ),
                qty_format_title,
                "",
            )
            i += 2

        # General totals
        sheet.write(i, 0, _("General Total"), title_style)
        sheet.write(i, 6, in_qty, qty_format_title)
        sheet.write(i, 7, out_qty, qty_format_title)
        sheet.write(i, 8, evaluation_amount, currency_format_title)
