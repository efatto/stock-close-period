from odoo import _, api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_cost_stock_move_lifo_fifo(self, closing_line_id, evaluation_method=False):
        product_id = closing_line_id.product_id
        company_id = closing_line_id.company_id.id
        # get start data from last close
        start_qty, start_price = self._get_last_closing(
            closing_line_id.close_id, product_id.id, company_id
        )
        res = self.price_calculation(
            closing_line_id,
            evaluation_method or closing_line_id.close_id.force_evaluation_method,
            start_qty,
            start_price,
        )
        res_dict = [
            {
                "product_id": x[0],
                "evaluated_qty": x[1],
                "price_unit": x[2],
                "moved_qty": x[3],
                "origin": x[4],
                "date": x[5],
            }
            for x in res
        ]
        line_total = closing_line_id._format_value(
            sum([x["evaluated_qty"] * x["price_unit"] for x in res_dict]),
        )
        closing_line_id.evaluation_details = "\n".join(
            [
                f"{x['origin'] or ''} - {x['date']}: "
                f"{closing_line_id._format_value(x['evaluated_qty'])} x "
                f"{closing_line_id._format_value(x['price_unit'])} = "
                f"{closing_line_id._format_value(x['evaluated_qty'] * x['price_unit'])}"
                for x in res_dict
            ]
            + [_(f"Total: {line_total}")]
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
            closing_line_id.price_unit = product_id._get_cost()
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
        if closing_id.force_evaluation_method in ["lifo", "fifo"]:
            self._get_cost_stock_move_lifo_fifo(closing_line_id)
        elif product_id.categ_id.property_cost_method == "fifo":
            self._get_cost_stock_move_lifo_fifo(closing_line_id, "fifo")
        else:
            super()._evaluate_product(
                closing_id, closing_line_id, last_close_date, product_id
            )

    @api.model
    def price_calculation(self, line, valuation_type, start_qty, start_price):
        line.ensure_one()
        order = "date desc, id desc"
        move_line_obj = self.env["stock.move.line"]
        # do not exclude inventory moves, as they are needed to compute qty at date
        move_line_domain = [
            ("state", "=", "done"),
            ("product_id", "=", line.product_id.id),
            ("qty_done", ">", 0),
            ("date", "<=", line.close_id.close_date),
            ("date", ">", line.close_id.last_close_date),
            ("active", "!=", False),
            ("company_id", "=", line.close_id.company_id.id),
        ]
        if valuation_type in ["fifo", "purchase"]:
            # search for incoming moves
            move_line_domain += [
                ("location_id.usage", "!=", "internal"),
                ("location_dest_id.usage", "=", "internal"),
                # todo solo per acquisti? ("purchase_line_id", "!=", False),
            ]
        else:
            # search for incoming and outgoing moves
            # fixme this search even internal moves
            move_line_domain += [
                "|",
                ("location_id.usage", "=", "internal"),
                ("location_dest_id.usage", "=", "internal"),
            ]
        move_line_ids = move_line_obj.search(move_line_domain, order=order)
        move_line_ids = sorted(
            [x for x in move_line_ids],
            key=lambda m: (
                m.date.strftime("%Y-%m-%d"),
                "a"
                if m.location_id.usage != "internal"
                and m.location_dest_id.usage == "internal"
                else "z",
            ),
            reverse=True,
        )
        res = self._get_tuples(
            line, move_line_ids, valuation_type, start_qty, start_price
        )
        return res

    @api.model
    def _get_tuples(self, line, move_line_ids, valuation_type, start_qty, start_price):
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
        :param move_line_ids:
        :param valuation_type:
        :return: a list of tuple with
        [(product_id, qty_to_be_evaluated, new_price, qty_from, origin, date)]
        """
        tuples = []
        qty_to_be_evaluated = line.product_qty
        qty_at_date = line.product_qty
        # get all moves without the lot in the inventory line because it is not relevant
        flag = False
        for ml in move_line_ids:
            uom_from = ml.move_id.product_uom
            # Convert to UoM of the product each time
            qty_from = ml.qty_done
            product_qty = uom_from._compute_quantity(qty_from, ml.product_id.uom_id)
            # Get price from the purchase line
            price_unit = 0
            if ml.move_id.purchase_line_id:
                price_unit = ml.move_id._get_purchase_price_unit()

            qty_to_be_evaluated, flag, qty_at_date = self.update_tuple(
                qty_to_be_evaluated,
                product_qty,
                tuples,
                ml,
                price_unit,
                qty_from,
                qty_at_date,
                valuation_type,
            )
            if flag:
                break
        if qty_to_be_evaluated:
            # create a tuple for the residual not evaluated
            tuples.append(
                (
                    line.product_id.id,
                    qty_to_be_evaluated,
                    start_price,
                    start_qty,
                    "Residual not evaluated",
                    "Date not evaluated",
                )
            )
        # fix zero values in the tuples
        tuples = self._fix_zero_values(tuples)
        return tuples

    def _fix_zero_values(self, tuples):
        fixed_tuples = []
        for i, raw_tuple in enumerate(tuples):
            if not raw_tuple[2]:
                # n.b. the order of the tuples is from the newer to the oldest
                if len(tuples) > i + 1 and tuples[i + 1] and tuples[i + 1][2]:
                    # 1. get the price from the previous evaluation tuple if exists
                    price_unit = tuples[i + 1][2]
                elif i != 0 and tuples[i - 1][2]:
                    # 2. get the price from the next evaluation tuple if not the first
                    price_unit = tuples[i - 1][2]
                else:
                    # 3. get the price from the product
                    price_unit = (
                        self.env["product.product"].browse(raw_tuple[0])._get_cost()
                    )
                fixed_tuples.append(
                    (
                        raw_tuple[0],
                        raw_tuple[1],
                        price_unit,
                        raw_tuple[3],
                        raw_tuple[4],
                        raw_tuple[5],
                    )
                )
            else:
                fixed_tuples.append(raw_tuple)
        return fixed_tuples

    @staticmethod
    def update_tuple(
        qty_to_be_evaluated,
        product_qty,
        tuples,
        ml,
        price_unit,
        qty_from,
        qty_at_date,
        valuation_type,
    ):
        if valuation_type == "fifo":
            if qty_to_be_evaluated - product_qty >= 0:
                tuples.append((ml.product_id.id, product_qty, price_unit, qty_from))
                qty_to_be_evaluated -= product_qty
            else:
                tuples.append(
                    (
                        ml.product_id.id,
                        qty_to_be_evaluated,
                        price_unit,
                        qty_from * qty_to_be_evaluated / product_qty,
                        ml.origin,
                        ml.date.strftime("%d/%m/%Y"),
                    )
                )
                return 0, True, qty_at_date
        elif valuation_type == "lifo":
            # create a tuple for every move that is an income (purchase or inventory)
            # not used for an outgoing with these values:
            # [(product.id, qty outgoing for this move, cost of purchased product,
            # qty moved)]
            # out (sale, out inventory, etc)
            if (
                ml.location_id.usage == "internal"
                and ml.location_dest_id.usage != "internal"
            ):
                qty_at_date += product_qty
            # in (purchase, in inventory, etc)
            if (
                ml.location_id.usage != "internal"
                and ml.location_dest_id.usage == "internal"
            ):
                qty_at_date -= product_qty
                # se la quantità da valorizzare è maggiore del saldo (maggiore di 0)
                # vuol dire che c'è un residuo di questo movimento non utilizzato e
                # quindi da inserire nella valorizzazione per la parte residua
                if qty_to_be_evaluated > qty_at_date > 0:
                    tuples.append(
                        (
                            ml.product_id.id,
                            qty_to_be_evaluated - qty_at_date,
                            price_unit,
                            qty_from,
                            ml.origin,
                            ml.date.strftime("%d/%m/%Y"),
                        )
                    )
                    qty_to_be_evaluated = qty_at_date
                # se la quantità da valorizzare è maggiore del saldo (pari a 0)
                # vuol dire che si può valorizzare tutto il residuo a questo importo
                elif qty_to_be_evaluated > qty_at_date <= 0:
                    tuples.append(
                        (
                            ml.product_id.id,
                            qty_to_be_evaluated,
                            price_unit,
                            qty_from * qty_to_be_evaluated / product_qty,
                            ml.origin,
                            ml.date.strftime("%d/%m/%Y"),
                        )
                    )
                    return 0, True, qty_at_date
        elif valuation_type == "average":
            tuples.append(
                (
                    ml.product_id.id,
                    product_qty,
                    price_unit,
                    qty_from,
                    ml.origin,
                    ml.date.strftime("%d/%m/%Y"),
                )
            )
        return qty_to_be_evaluated, False, qty_at_date
