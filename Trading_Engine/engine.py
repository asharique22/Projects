import heapq
import itertools

class MatchingEngine:
    def __init__(self):
        self.buys = []
        self.sells = []
        self.order_id = itertools.count()

    def add_order(self, side, qty, price, trader_id="Unknown"):
        order = {
            "id": next(self.order_id),
            "side": side,
            "qty": int(qty),
            "price": float(price),
            "trader_id": trader_id,
        }
        trades = []

        if side == "BUY":
            while self.sells and order["qty"] > 0:
                best_sell_price, _, best_sell = self.sells[0]
                if order["price"] >= best_sell_price and best_sell["qty"] > 0:
                    heapq.heappop(self.sells)
                    trade_qty = min(order["qty"], best_sell["qty"])
                    trades.append({
                        "qty": trade_qty,
                        "price": best_sell_price,
                        "buyer": order["trader_id"],
                        "seller": best_sell["trader_id"],
                    })
                    order["qty"] -= trade_qty
                    best_sell["qty"] -= trade_qty
                    if best_sell["qty"] > 0:
                        heapq.heappush(self.sells, (best_sell_price, best_sell["id"], best_sell))
                else:
                    break

            if order["qty"] > 0:
                heapq.heappush(self.buys, (-order["price"], order["id"], order))

        else:
            while self.buys and order["qty"] > 0:
                neg_best_buy_price, _, best_buy = self.buys[0]
                best_buy_price = -neg_best_buy_price
                if best_buy_price >= order["price"] and best_buy["qty"] > 0:
                    heapq.heappop(self.buys)
                    trade_qty = min(order["qty"], best_buy["qty"])
                    trades.append({
                        "qty": trade_qty,
                        "price": best_buy_price,
                        "buyer": best_buy["trader_id"],
                        "seller": order["trader_id"],
                    })
                    order["qty"] -= trade_qty
                    best_buy["qty"] -= trade_qty
                    if best_buy["qty"] > 0:
                        heapq.heappush(self.buys, (-best_buy_price, best_buy["id"], best_buy))
                else:
                    break

            if order["qty"] > 0:
                heapq.heappush(self.sells, (order["price"], order["id"], order))

        return trades
