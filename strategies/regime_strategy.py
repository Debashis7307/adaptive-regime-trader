import backtrader as bt

from config import ATR_PERIOD, BREAKOUT_PERIOD, EMA_PERIOD, RSI_PERIOD


class RegimeStrategy(bt.Strategy):

    params = (
        ("ema_period", EMA_PERIOD),
        ("rsi_period", RSI_PERIOD),
        ("atr_period", ATR_PERIOD),
        ("breakout_period", BREAKOUT_PERIOD),
        ("rsi_threshold", 50),
        ("atr_multiplier", 2.0),
        ("trade_start", None),
    )

    def __init__(self):
        self.ema = bt.indicators.EMA(self.data.close, period=self.p.ema_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.breakout_period)
        self.order = None
        self.stop_price = None

    def _trading_allowed(self):
        if self.p.trade_start is None:
            return True
        return self.data.datetime.date(0) >= self.p.trade_start

    def _target_size(self):
        cash = self.broker.get_cash()
        price = self.data.close[0]
        if price <= 0:
            return 0
        return int(cash * 0.95 / price)

    def next(self):
        if self.order or not self._trading_allowed():
            return

        in_uptrend = self.data.close[0] > self.ema[0]

        if not self.position:
            if not in_uptrend:
                return
            if self.rsi[0] > self.p.rsi_threshold and self.data.close[0] >= self.highest[-1]:
                size = self._target_size()
                if size <= 0:
                    return
                self.order = self.buy(size=size)
                self.stop_price = self.data.close[0] - self.atr[0] * self.p.atr_multiplier
        else:
            trailing = self.data.close[0] - self.atr[0] * self.p.atr_multiplier
            self.stop_price = max(self.stop_price, trailing)
            if self.data.close[0] < self.stop_price:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None
