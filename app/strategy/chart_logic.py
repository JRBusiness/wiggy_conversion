from datetime import datetime
from typing import Optional

import pandas as pd
import pytz
from loguru import logger
from matplotlib import pyplot as plt
from pydantic import BaseModel


class CandleData(BaseModel):
    symbol: Optional[str]
    time: Optional[datetime] = datetime.now(pytz.utc)
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    tick_volume: Optional[int]
    spread: Optional[int]
    real_volume: Optional[int]
    ema_length: Optional[int]
    gap_window: Optional[int]
    bar_limit: Optional[int]
    pip_threshold: Optional[int]
    fib_59: Optional[float]
    fib_163: Optional[float]
    buy_condition: Optional[bool]
    sell_condition: Optional[bool]
    wick_size: Optional[float]
    buy_wick_condition: Optional[bool]
    sell_wick_condition: Optional[bool]


def run_analysis(
    candle_data: pd.DataFrame, point_value: float, show_plot=False
) -> Optional[CandleData]:
    """
    The run_analysis function takes a dataframe of candle data and the point value for the symbol.
    It then calculates various indicators, including EMA, price-EMA gap, wick size and buy/sell conditions.
    The function returns a CandleData object containing all of these values.

    Args:
        candle_data: pd.DataFrame: Pass the dataframe of candle data into the function
        point_value: float: Convert the wick size from pips to dollars

        Returns:
            A CandleData object

    """
    pip_threshold = 10
    ema_length = 100
    gap_window = 100
    bar_limit = 1000

    # check if the dataframe is empty
    if not candle_data or candle_data.size <= 0:
        logger.info("Dataframe is empty")
        return

    # Check if the dataframe is long enough to calculate the indicators

    if candle_data.shape[0] < ema_length:
        ema_length = candle_data.shape[0]
    if candle_data.shape[0] < gap_window:
        gap_window = candle_data.shape[0]
    if candle_data.shape[0] < bar_limit:
        bar_limit = candle_data.shape[0]

    # Calculate EMA
    candle_data["ema_long"] = candle_data["close"].ewm(span=ema_length).mean()

    # Calculate price-EMA gap
    candle_data["gap"] = candle_data["close"] - candle_data["ema_long"]

    # Find the longest gap
    candle_data["longest_gap"] = candle_data["gap"].rolling(window=gap_window).max()

    # Determine buy/sell conditions
    candle_data["buy_condition"] = candle_data["gap"] < 0
    candle_data["sell_condition"] = candle_data["gap"] > 0

    # Calculate wick size
    candle_data["wick_size"] = (
        abs(candle_data["high"] - candle_data["low"]) / point_value
    )

    # Check conditions for buy and sell wicks
    candle_data["buy_wick_condition"] = candle_data["buy_condition"] & (
        candle_data["wick_size"] >= pip_threshold
    )
    candle_data["sell_wick_condition"] = candle_data["sell_condition"] & (
        candle_data["wick_size"] >= pip_threshold
    )

    # Calculate the number of buy and sell wicks
    candle_data["buy_wick_count"] = (
        candle_data["buy_wick_condition"].rolling(window=bar_limit).sum()
    )
    candle_data["sell_wick_count"] = (
        candle_data["sell_wick_condition"].rolling(window=bar_limit).sum()
    )

    # run a fib from the previous low to the previous high  and store levels  of 59% and 163%
    candle_data["fib_59"] = (
        candle_data["low"].shift(1)
        + (candle_data["high"].shift(1) - candle_data["low"].shift(1)) * 0.59
    )
    candle_data["fib_163"] = (
        candle_data["low"].shift(1)
        + (candle_data["high"].shift(1) - candle_data["low"].shift(1)) * 1.63
    )

    if show_plot:
        plot_data(candle_data)

    return CandleData(**candle_data.iloc[-1].to_dict())


def plot_data(candle_data):
    """
    The plot_data function takes a dataframe of candle data and plots the data and indicators.
    :param candle_data:
    :return:  A CandleData object
    """
    # show a plot of the data and highlight the fib levels and the entry and exit positions
    candle_data.plot(y=["close", "ema_long", "fib_59", "fib_163"], figsize=(20, 10))
    candle_data.plot(y=["buy_wick_count", "sell_wick_count"], figsize=(20, 10))
    candle_data.plot(y=["gap", "longest_gap"], figsize=(20, 10))
    candle_data.plot(y=["wick_size"], figsize=(20, 10))
    # candle_data.plot(y=['buy_wick_condition', 'sell_wick_condition'], figsize=(20, 10))
    # candle_data.plot(y=['buy_condition', 'sell_condition'], figsize=(20, 10))
    candle_data.plot(y=["ema_long"], figsize=(20, 10))
    candle_data.plot(y=["gap"], figsize=(20, 10))
    # plot the fibs
    candle_data.plot(y=["fib_59", "fib_163"], figsize=(20, 10))
    candle_data.plot(y=["fib_59", "fib_163", "close"], figsize=(20, 10))
    candle_data.plot(y=["fib_59", "fib_163", "close"], figsize=(20, 10))

    # show the plot
    plt.show()


if __name__ == "__main__":
    for symbol in qualified_symbols:
        item = mt5.symbol_info(symbol.symbol)
        point = item.point
        # print(symbol.symbol, symbol.df.close.iloc[-1], point)
        run_analysis(symbol.df, point_value=point)