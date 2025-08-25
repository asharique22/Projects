import heapq
import itertools

class MatchingEngine:
    
    def __init__(self):
        self.buys = []
        self.sells = []
        self.order_id = itertools.count()

    # it adds a new order to the book and attempts to match it
    def add_order(self, side, qty, price):
        order = {"id": next(self.order_id), "side": side, "qty": qty, "price": price}

        if side == "BUY":
            heapq.heappush(self.buys, (-price, order["id"], order))
            trades = self._match_buy(order)
        else:
            heapq.heappush(self.sells, (price, order["id"], order))
            trades = self._match_sell(order)

        return trades

    
    def _match_buy(self, order):
        trades = []
        while self.sells and order["qty"] > 0:
            best_sell_price, _, best_sell = self.sells[0]
            if order["price"] >= best_sell_price:
                heapq.heappop(self.sells)
                trade_qty = min(order["qty"], best_sell["qty"])
                trades.append({"qty": trade_qty, "price": best_sell_price})
                order["qty"] -= trade_qty
                best_sell["qty"] -= trade_qty
                if best_sell["qty"] > 0:
                    heapq.heappush(self.sells, (best_sell_price, best_sell["id"], best_sell))
            else:
                break
        return trades

    def _match_sell(self, order):
        trades = []
        while self.buys and order["qty"] > 0:
            best_buy_price, _, best_buy = self.buys[0]
            best_buy_price = -best_buy_price
            if order["price"] <= best_buy_price:
                heapq.heappop(self.buys)
                trade_qty = min(order["qty"], best_buy["qty"])
                trades.append({"qty": trade_qty, "price": best_buy_price})
                order["qty"] -= trade_qty
                best_buy["qty"] -= trade_qty
                if best_buy["qty"] > 0:
                    heapq.heappush(self.buys, (-best_buy_price, best_buy["id"], best_buy))
            else:
                break
        return trades
