import talib
from typing import List, Union


class Strategy:
    def __init__(self):
        self.signals = []
        self.bband_length = 20
        self.bband_stddev = 2
        self.ema9_length = 9
        self.ema26_length = 26
        self.ema100_length = 100
        self.fibonacci_retrace = 0.618
        self.lowerWickPercent = 1
        self.bodyPercent = 1

    def fetch_market_data(self, symbols: List[dict]):
        # Fetch market data for the given symbols using mt5

        # Perform any necessary data processing or filtering

        # Assign the fetched data to self.signals
        self.signals = symbols

    def perform_strategy_calculations(self):
        for symbol in self.signals:
            close = symbol["close"]
            open = symbol["open"]
            high = symbol["high"]
            low = symbol["low"]
            ema9 = talib.EMA(close, timeperiod=self.ema9_length)
            ema26 = talib.EMA(close, timeperiod=self.ema26_length)
            ema100 = talib.EMA(close, timeperiod=self.ema100_length)
            bbandUpper, bbandMiddle, bbandLower = talib.BBANDS(
                close,
                timeperiod=self.bband_length,
                nbdevup=self.bband_stddev,
                nbdevdn=self.bband_stddev,
            )
            atr = talib.ATR(high, low, close, timeperiod=14)

            # Calculate the conditions for signal generation
            lowerWick = low - talib.MIN(open, close)
            bodySize = abs(close - open)
            candleSize = high - low
            upperWick = high - talib.MAX(open, close)

            wickCondition = lowerWick > self.lowerWickPercent * open / 100
            bodyCondition = bodySize < self.bodyPercent * candleSize
            redBarsCondition = (
                close < open and close[1] < open[1] and close[2] < open[2]
            )
            greenCandleCondition = close > open[1]
            volatilityCondition = high - low > bbandUpper - bbandLower
            emasCondition = (close < ema9 and close < ema26 and close > ema100) or (
                close > ema100 and close[1] < ema100
            )

            # Generate signals based on the calculated conditions
            if (
                symbol["wickTrigger"]
                and wickCondition
                and bodyCondition
                and redBarsCondition
            ):
                symbol["signal"] = "BUY"
            elif symbol["greenCandleTrigger"] and greenCandleCondition:
                symbol["signal"] = "BUY"
            elif symbol["volatilityTrigger"] and volatilityCondition and emasCondition:
                symbol["signal"] = "SELL"
            else:
                symbol["signal"] = "NONE"

    def optimization_func(self, params: List[Union[int, float]]) -> float:
        (
            self.bband_length,
            self.bband_stddev,
            self.ema9_length,
            self.ema26_length,
            self.ema100_length,
            self.fibonacci_retrace,
        ) = params

        self.perform_strategy_calculations()

        # Calculate the fitness score based on the optimization goal (e.g., win rate, lowest drawdown)
        fitness_score = 1.0

        return -fitness_score
