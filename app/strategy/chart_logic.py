from datetime import datetime
from typing import Optional

import pandas as pd
import pytz
import ta
from loguru import logger
import plotly.graph_objects as go
import MetaTrader5 as mt5

from utility import calculate_ema, calculate_bollinger_bands, calculate_rsi


class CandleData:
    def __init__(
        self,
        symbol: Optional[str],
        time: Optional[datetime] = datetime.now(pytz.utc),
        open: Optional[float] = None,
        high: Optional[float] = None,
        low: Optional[float] = None,
        close: Optional[float] = None,
        tick_volume: Optional[int] = None,
        spread: Optional[int] = None,
        real_volume: Optional[int] = None,
        ema_length: Optional[int] = None,
        gap_window: Optional[int] = None,
        bar_limit: Optional[int] = None,
        pip_threshold: Optional[int] = None,
        fib_59: Optional[float] = None,
        fib_163: Optional[float] = None,
        buy_condition: Optional[bool] = None,
        sell_condition: Optional[bool] = None,
        wick_size: Optional[float] = None,
        buy_wick_condition: Optional[bool] = None,
        sell_wick_condition: Optional[bool] = None,
        ema_long: Optional[float] = None,
    ):
        self.symbol = symbol
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.tick_volume = tick_volume
        self.spread = spread
        self.real_volume = real_volume
        self.ema_length = ema_length
        self.gap_window = gap_window
        self.bar_limit = bar_limit
        self.pip_threshold = pip_threshold
        self.fib_59 = fib_59
        self.fib_163 = fib_163
        self.buy_condition = buy_condition
        self.sell_condition = sell_condition
        self.wick_size = wick_size
        self.buy_wick_condition = buy_wick_condition
        self.sell_wick_condition = sell_wick_condition
        self.ema_long = ema_long


def validate_data(candle_data: pd.DataFrame) -> bool:
    required_columns = [
        "symbol",
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
    ]
    for column in required_columns:
        if column not in candle_data.columns:
            logger.error(f"Required column '{column}' is missing.")
            return False
    return True


def run_analysis(candle_data: pd.DataFrame, point_value: float, show_plot=False) -> Optional[CandleData]:
    pip_threshold = 10
    ema_length = 100
    gap_window = 100
    bar_limit = 1000

    if not validate_data(candle_data):
        return

    if candle_data.shape[0] < ema_length:
        ema_length = candle_data.shape[0]
    if candle_data.shape[0] < gap_window:
        gap_window = candle_data.shape[0]
    if candle_data.shape[0] < bar_limit:
        bar_limit = candle_data.shape[0]
    ema_high = calculate_ema(candle_data['high'], ema_length)
    ema_low = calculate_ema(candle_data['low'], ema_length)
    candle_data["ema_high"] = ema_high
    candle_data["ema_low"] = ema_low
    try:
        ema_long = calculate_ema(candle_data, ema_length)  # Calculate EMA
        candle_data["ema_long"] = ema_long
        candle_data["gap"] = candle_data["close"] - ema_long
        candle_data["longest_gap"] = candle_data["gap"].rolling(window=gap_window).max()
        candle_data["buy_condition"] = candle_data["gap"] < 0
        candle_data["sell_condition"] = candle_data["gap"] > 0
        candle_data["wick_size"] = abs(candle_data["high"] - candle_data["low"]) / point_value
        candle_data["buy_wick_condition"] = candle_data["buy_condition"] & (candle_data["wick_size"] >= pip_threshold)
        candle_data["sell_wick_condition"] = candle_data["sell_condition"] & (candle_data["wick_size"] >= pip_threshold)
        candle_data["buy_wick_count"] = candle_data["buy_wick_condition"].rolling(window=bar_limit).sum()
        candle_data["sell_wick_count"] = candle_data["sell_wick_condition"].rolling(window=bar_limit).sum()
        candle_data["fib_59"] = (
            candle_data["low"].shift(1)
            + (candle_data["high"].shift(1) - candle_data["low"].shift(1)) * 0.59
        )
        candle_data["fib_163"] = (
            candle_data["low"].shift(1)
            + (candle_data["high"].shift(1) - candle_data["low"].shift(1)) * 1.63
        )

        candle_data['atr'] = ta.volatility.average_true_range(candle_data['high'], candle_data['low'],
                                                              candle_data['close'],
                                                              n=14)
        candle_data['rsi'] = ta.momentum.rsi(candle_data['close'], n=14)
        if show_plot:
            # Ensure the data is sorted by index before plotting
            candle_data = candle_data.sort_index()
            plot_data(candle_data)

        last_row = candle_data.iloc[-1]
        return CandleData(
            symbol=last_row["symbol"],
            time=last_row["time"],
            open=last_row["open"],
            high=last_row["high"],
            low=last_row["low"],
            close=last_row["close"],
            tick_volume=last_row["tick_volume"],
            spread=last_row["spread"],
            real_volume=last_row["real_volume"],
            ema_length=ema_length,
            gap_window=gap_window,
            bar_limit=bar_limit,
            pip_threshold=pip_threshold,
            fib_59=last_row["fib_59"],
            fib_163=last_row["fib_163"],
            buy_condition=last_row["buy_condition"],
            sell_condition=last_row["sell_condition"],
            wick_size=last_row["wick_size"],
            buy_wick_condition=last_row["buy_wick_condition"],
            sell_wick_condition=last_row["sell_wick_condition"],
            ema_long=last_row["ema_long"],
        )

    except Exception as e:
        logger.error(f"Error occurred during analysis: {str(e)}")


def plot_data(candle_data, indicators=None):
    """
    The plot_data function takes a dataframe of candle data and plots the data and indicators.
    :param candle_data: pd.DataFrame: The dataframe of candle data
    :param indicators: List[str]: List of indicators or data columns to plot
    :return: None
    """
    if indicators is None:
        indicators = ["close", "ema_long", "fib_59", "fib_163"]

    fig = go.Figure(data=[go.Candlestick(x=candle_data.index,
                                         open=candle_data['open'],
                                         high=candle_data['high'],
                                         low=candle_data['low'],
                                         close=candle_data['close'])])

    for indicator in indicators:
        fig.add_trace(go.Scatter(x=candle_data.index, y=candle_data[indicator], name=indicator))

    fig.update_layout(title="Candle Data", xaxis_title="Date", yaxis_title="Value")
    fig.show()

if __name__ == "__main__":
    data = {
        "symbol": ["AAPL", "AAPL", "AAPL", "AAPL"],
        "time": [
            datetime(2022, 1, 1, tzinfo=pytz.utc),
            datetime(2022, 1, 2, tzinfo=pytz.utc),
            datetime(2022, 1, 3, tzinfo=pytz.utc),
            datetime(2022, 1, 4, tzinfo=pytz.utc),
        ],
        "open": [100.0, 101.0, 102.0, 103.0],
        "high": [105.0, 106.0, 107.0, 108.0],
        "low": [95.0, 96.0, 97.0, 98.0],
        "close": [103.0, 104.0, 105.0, 106.0],
        "tick_volume": [1000, 2000, 3000, 4000],
        "spread": [0, 0, 0, 0],
        "real_volume": [10000, 20000, 30000, 40000],
    }
    run_analysis(pd.DataFrame(data), 0.1, show_plot=True)