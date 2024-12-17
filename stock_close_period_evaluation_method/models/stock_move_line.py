from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_cost_stock_move_fifo(self, last_close_date, closing_line_id):
        pass

    def _get_cost_stock_move_lifo(self, last_close_date, closing_line_id, closing_id):
        product_id = closing_line_id.product_id
        company_id = closing_line_id.company_id.id
        # get start data from last close
        start_qty, start_price = self._get_last_closing(
            closing_line_id.close_id, product_id.id, company_id
        )
        res = self.price_calculation(
            closing_line_id, closing_id.force_evaluation_method, start_qty, start_price
        )
        cumulative_amount = 0
        cumulative_qty = 0
        qty_moved = 0

        for match in res:
            qty_to_be_evaluated = match[1]
            price = match[2]
            qty = match[3]
            qty_moved += qty
            cumulative_amount += qty_to_be_evaluated * price
            cumulative_qty += qty_to_be_evaluated
        price_unit = (cumulative_amount / cumulative_qty) if cumulative_qty else 0.0

        if start_qty:
            inventory_amount = start_price * start_qty
            inventory_qty = start_qty
        else:
            inventory_amount = 0
            inventory_qty = 0

        cumulative_landed_cost = 0

        #     additional_landed_cost_new = self._get_additional_landed_cost_new(
        #         move_id, company_id
        #     )
        #     cumulative_landed_cost += additional_landed_cost_new

        if price_unit == 0:
            closing_line_id.price_unit = product_id.standard_price
            closing_line_id.evaluation_method = "standard"
        else:
            closing_line_id.price_unit = price_unit
            closing_line_id.inventory_amount = inventory_amount
            closing_line_id.inventory_qty = inventory_qty
            closing_line_id.cumulative_amount = cumulative_amount
            closing_line_id.cumulative_landed_cost = cumulative_landed_cost
            closing_line_id.cumulative_qty = cumulative_qty
            closing_line_id.evaluation_method = "purchase"

    @api.model
    def _evaluate_product(
        self, closing_id, closing_line_id, last_close_date, product_id
    ):
        if closing_id.force_evaluation_method == "lifo":
            self._get_cost_stock_move_lifo(last_close_date, closing_line_id, closing_id)
        elif (
            closing_id.force_evaluation_method == "fifo"
            or product_id.categ_id.property_cost_method == "fifo"
        ):
            self._get_cost_stock_move_fifo(last_close_date, closing_line_id)
        else:
            super()._evaluate_product(
                closing_id, closing_line_id, last_close_date, product_id
            )

    @api.model
    def price_calculation(self, line, valuation_type, start_qty, start_price):
        line.ensure_one()
        order = "date desc, id desc"
        move_obj = self.env["stock.move"]
        move_domain = [
            ("state", "=", "done"),
            ("product_id", "=", line.product_id.id),
            ("product_qty", ">", 0),
            ("date", "<=", line.close_id.close_date),
            ("active", "!=", False),
            ("company_id", "=", line.close_id.company_id.id),
        ]
        if line.close_id.last_closed_id:
            move_domain += [("date", ">", line.close_id.last_closed_id.close_date)]
        if valuation_type in ["fifo", "purchase"]:
            # search for incoming moves
            move_domain += [
                ("location_id.usage", "!=", "internal"),
                ("location_dest_id.usage", "=", "internal"),
                # todo solo per acquisti? ("purchase_line_id", "!=", False),
            ]
        else:
            # search for incoming and outgoing moves
            # fixme this search even internal moves
            move_domain += [
                "|",
                ("location_id.usage", "=", "internal"),
                ("location_dest_id.usage", "=", "internal"),
            ]
        move_ids = move_obj.search(move_domain, order=order)
        res = self._get_tuples(line, move_ids, valuation_type, start_qty, start_price)
        return res

    @api.model
    def _get_tuples(self, line, move_ids, valuation_type, start_qty, start_price):
        """
        - calcolare il valore sulla differenza positiva tra in minimo iniziale e
        il precedente se più alto [ degli stock_move in ingresso ordinati per
        data decrescente prima della fine del periodo in stato "done" ] [dei
        prodotti con quantità attuale > 0 ] [qty_to_be_evaluated è la rimanenza attuale]
        [qty_from sono le qty delle varie moves]
        quindi:
        se qty_to_be_evaluated - qty_from >= 0 [uguale ?]
        tuples.append(move.id, qty_to_be_evaluated - qty_from, new_price, qty_from)
        se < 0
        tuples.append(move.id [product ?], qty_to_be_evaluated, new_price,
         qty_from [* qty_to_be_evaluated ?]
        inv acq vend
        2
                1
            4
            5
        tot 10
        se 10-5>=0: 5x€ attuale
        se 5-4>=0: 4x€ attuale
        se 1-2>=0: no! quindi 1x€ ?

        LIFO: retrocedere fino alla quantità a magazzino 0 oppure all'ultima chiusura
        di magazzino e valutare il residuo al costo di acquisto relativo ad ogni minimo
        residuo.

        - consumabili: no nell'inventario
        :param line:
        :param move_ids:
        :param valuation_type:
        :return:
        """
        tuples = []
        qty_to_be_evaluated = line.product_qty
        qty_at_date = line.product_qty
        # get all move without lot of inventory line because it is not relevant
        flag = False
        for move in move_ids:
            uom_from = move.product_uom
            for ml in move.move_line_ids:
                # Convert to UoM of product each time
                qty_from = ml.qty_done
                product_qty = uom_from._compute_quantity(
                    qty_from, move.product_id.uom_id
                )
                # Get price from purchase line
                price_unit = 0
                if move.purchase_line_id:
                    if (
                        move.purchase_line_id.invoice_lines
                        and move.purchase_line_id.invoice_lines[0].move_id.state
                        == "posted"
                    ):
                        # In real life, all move lines related to an 1 invoice line
                        # should be in the same state and have the same date
                        inv_line = move.purchase_line_id.invoice_lines[0]
                        invoice = inv_line.move_id
                        price_unit = invoice.currency_id._convert(
                            inv_line.price_subtotal,
                            invoice.company_id.currency_id,
                            invoice.company_id,
                            invoice.date or fields.Date.today(),
                        ) / (inv_line.quantity if inv_line.quantity != 0 else 1)
                    else:
                        # get price from purchase line
                        purchase = move.purchase_line_id.order_id
                        price_unit = purchase.currency_id._convert(
                            move.purchase_line_id.price_subtotal,
                            purchase.company_id.currency_id,
                            purchase.company_id,
                            purchase.date_order or fields.Date.today(),
                        ) / (
                            move.purchase_line_id.product_qty
                            if move.purchase_line_id.product_qty != 0
                            else 1
                        )
                if (
                    move.location_id.usage == "internal"
                    and move.location_dest_id.usage != "internal"
                    and not price_unit
                ):
                    # Get price from product, move is a production or a sale or an
                    # inventory or not linked to a purchase
                    # (income move created and even invoiced, but price is not valid)
                    price_unit = move.product_id.standard_price

                qty_to_be_evaluated, flag, qty_at_date = self.update_tuple(
                    qty_to_be_evaluated,
                    product_qty,
                    tuples,
                    move,
                    price_unit,
                    qty_from,
                    qty_at_date,
                    valuation_type,
                    start_qty,
                    start_price,
                )
                if flag:
                    break
            if not move.move_line_ids:
                price_unit = move.product_id.standard_price
                qty_from = move.product_qty
                product_qty = uom_from._compute_quantity(
                    qty_from, move.product_id.uom_id
                )
                qty_to_be_evaluated, flag, qty_at_date = self.update_tuple(
                    qty_to_be_evaluated,
                    product_qty,
                    tuples,
                    move,
                    price_unit,
                    qty_from,
                    qty_at_date,
                    valuation_type,
                    start_qty,
                    start_price,
                )
            if flag:
                break
        if qty_to_be_evaluated:
            # create a tuple for the residual not evaluated
            tuples.append(
                (line.product_id.id, qty_to_be_evaluated, start_price, start_qty)
            )
        return tuples

    @staticmethod
    def update_tuple(
        qty_to_be_evaluated,
        product_qty,
        tuples,
        move,
        price_unit,
        qty_from,
        qty_at_date,
        valuation_type,
        start_qty,
        start_price,
    ):
        if valuation_type == "fifo":
            if qty_to_be_evaluated - product_qty >= 0:
                tuples.append((move.product_id.id, product_qty, price_unit, qty_from))
                qty_to_be_evaluated -= product_qty
            else:
                tuples.append(
                    (
                        move.product_id.id,
                        qty_to_be_evaluated,
                        price_unit,
                        qty_from * qty_to_be_evaluated / product_qty,
                    )
                )
                return 0, True, qty_at_date
        elif valuation_type == "lifo":
            # create a tuple for every move which is an income (purchase or inventory)
            # not used for an outgoing with these values:
            # [(product.id, qty outgoing for this move, cost of purchased product, qty moved)]
            # sale
            if (
                move.location_id.usage == "internal"
                and move.location_dest_id.usage != "internal"
            ):
                qty_at_date += product_qty
            # purchase
            if (
                move.location_id.usage != "internal"
                and move.location_dest_id.usage == "internal"
            ):
                qty_at_date -= product_qty
                # se la quantità da valorizzare è maggiore del saldo (maggiore di 0)
                # vuol dire che c'è un residuo di questo movimento non utilizzato e
                # quindi da inserire nella valorizzazione per la parte residua
                if qty_to_be_evaluated > qty_at_date > 0:
                    tuples.append(
                        (
                            move.product_id.id,
                            qty_to_be_evaluated - qty_at_date,
                            price_unit,
                            qty_from,
                        )
                    )
                    qty_to_be_evaluated = qty_at_date
                # se la quantità da valorizzare è maggiore del saldo (pari a 0)
                # vuol dire che si può valorizzare tutto il residuo a questo importo
                elif qty_to_be_evaluated > qty_at_date <= 0:
                    tuples.append(
                        (
                            move.product_id.id,
                            qty_to_be_evaluated,
                            price_unit,
                            qty_from * qty_to_be_evaluated / product_qty,
                        )
                    )
                    return 0, True, qty_at_date
        elif valuation_type == "average":
            tuples.append((move.product_id.id, product_qty, price_unit, qty_from))
        return qty_to_be_evaluated, False, qty_at_date
