import asyncio
import sys
import time
from typing import List

import pytz
from loguru import logger
import MetaTrader5 as mt5
import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, BaseConfig, Field, Extra
from datetime import datetime
from chart_logic import CandleData, run_analysis
from tqdm import tqdm

logger.configure(
    handlers=[
        dict(sink=lambda msg: tqdm.write("", end=""), format="\n{message}"),
        dict(sink="logs/strategy.log", encoding="utf-8", retention="10 days"),
        dict(sink=sys.stdout, level="DEBUG", backtrace=True, diagnose=True)
    ]

)



class NoTickDataException(BaseException):
    """
    This class is the exception class for no tick data
    """

    def __init__(self):
        """
        This function is the constructor of the class
        """
        super().__init__("No tick data found")

class NoCandleDataException(BaseException):
    """
    This class is the exception class for no candle data
    """

    def __init__(self):
        """
        This function is the constructor of the class
        """
        super().__init__("No candle data found")

class NoDataException(BaseException):

    def __init__(self):
        """
        This function is the constructor of the class
        """
        super().__init__("No data found")


class NoOrderException(BaseException):

    def __init__(self):
        """
        This function is the constructor of the class
        """
        super().__init__("No order found")

class NoPositionException(BaseException):

    def __init__(self):
        """
        This function is the constructor of the class
        """
        super().__init__("No position found")


class NoHistoryException(BaseException):

        def __init__(self):
            """
            This function is the constructor of the class
            """
            super().__init__("No history found")

class NoAccountException(BaseException):
    pass





class MT5Strategy(BaseModel):
    """
    This class is the base class for all strategies
    """
    symbol: str = Field(default=None, description="Symbol to trade")
    lot_size: float = Field(default=None, description="Lot size to trade")
    timeframe: str = Field(default=None, description="Timeframe to trade")
    start_time: datetime = Field(default=None, description="Start time of the strategy")
    end_time: datetime = Field(default=None, description="End time of the strategy")
    df: pd.DataFrame = Field(default=None, description="Dataframe containing the data for the strategy")
    position: str = Field(default=None, description="Position of the strategy")
    count: int = Field(default=None, description="Count of the strategy")


    class Config(BaseConfig):
        arbitrary_types_allowed = True
        extra = Extra.allow

    def __new__(cls, *args, **kwargs):
        """
        This function is the constructor of the class
        """
        for key, value in kwargs.items():
            cls.__setattr__(MT5Strategy(), key, value)
            # logger.info(f"Setting {key} to {value}")
        return super().__new__(cls)

    def fetch_data(self) -> pd.DataFrame:
        """
        The fetch_data function is used to fetch data from the MetaTrader 5 API.

        Args:
            cls:  Pass the class object to the function

        Returns:
            A pandas dataframe with the following columns:


        """
        logger.info(self)

        logger.info(self.symbol, self.timeframe, self.start_time, self.end_time)
        timezone = pytz.timezone("Etc/UTC")
        utc_from = self.start_time.replace(tzinfo=timezone)
        utc_to = self.end_time.replace(tzinfo=timezone)

        try:
            return self.fetch_range(utc_from, utc_to)
        except Exception as e:
            logger.error(f"copy_rates_range() failed, error code={mt5.last_error()}")
            logger.error(e)


    def fetch_range(self, utc_from: datetime, utc_to: datetime) -> pd.DataFrame:
        rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M5, utc_from, utc_to)
        if not len(rates):
            rates = mt5.copy_rates_from(self.symbol, mt5.TIMEFRAME_M5, utc_from, 100)
            logger.info(rates)

        if not len(rates):
            logger.info(mt5.last_error())
            raise NoTickDataException()

        df = pd.DataFrame(rates, columns=['time', 'open', 'high', 'low', 'close', 'volume']).set_index('time')
        df.index = pd.to_datetime(df.index, unit='s')
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df['symbol'] = self.symbol
        logger.info(f"Data fetched for {df['symbol'] }")
        df['lot_size'] = self.lot_size
        df['timeframe'] = self.timeframe
        df['start_time'] = self.start_time
        df['end_time'] = self.end_time
        logger.info(f"Dataframe shape: {df.shape}")
        logger.info(f"Dataframe head: {df.head(5)}")
        return df

    # def scan_market(cls):
    #     """
    #     This function scans the market for qualified symbols
    #     :return:
    #     """
        #
        # symbols_info = mt5.symbols_get()
        #
        #
        # data = cls.multiprocess_data(symbols_info, 500, start_time=datetime(2023, 1, 1), end_time=datetime(2023, 1, 2))
        # for symbol in symbols:
        #     obj = cls(
        #         symbol=symbol.name,
        #         lot_size=0.01,
        #         timeframe=mt5.TIMEFRAME_M5,
        #         start_time=datetime(2023, 1, 1),
        #         end_time=datetime(2023, 1, 2)
        #     )


    def send_order(self, order_type, price):
        """
        This function sends an order to MT5
        :param order_type:
        :param price:
        :return:
        """
        trade_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot_size,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": f"{order_type} order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(trade_request)
        logger.info(
            f"order_send(): {order_type} {self.symbol} {self.lot_size} lots at {price} with deviation=20 points")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.parse_mt5_result(result)
        logger.info(f"order_send done, {result}")
        self.position = order_type

    @classmethod
    def parse_mt5_result(cls, result):
        """
        This function parses the result of an order request and logs the fields
        :param result: The result of an order request
        """
        logger.error(f"order_send failed, retcode={result.retcode}")
        result_dict = result._asdict()
        for field in result_dict.keys():
            logger.error(f" {field}={result_dict[field]}")
            if field == "request":
                trade_request_dict = result_dict[field]._asdict()
                for req_field in trade_request_dict:
                    logger.error(f" trade_request: {req_field}={trade_request_dict[req_field]}")
        # logger.error("shutdown() and quit")
        # mt5.shutdown()
        # quit()

    def close_and_reverse(self, order_type, price):
        """
        This function closes the current position and opens a new position
        :param order_type:
        :param price:
        :return:
        """
        # Close current position
        close_type = mt5.ORDER_TYPE_SELL if self.position == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        self.send_order(close_type, price)



    def run_strategy(self):
        """
        This function runs the strategy on the historical data
        :return:
        """
        for i, row in self.df.iterrows():
            if i < 1:  # Skip the first row
                continue
            if row['buy_wick_condition'] and self.position != mt5.ORDER_TYPE_BUY:
                self.close_and_reverse(mt5.ORDER_TYPE_BUY, row['close'])
            elif row['sell_wick_condition'] and self.position != mt5.ORDER_TYPE_SELL:
                self.close_and_reverse(mt5.ORDER_TYPE_SELL, row['close'])


def chunker(seq, size):
    """
    This function is used to chunk the data
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def split(df, chunk_size):
    """
    This function is used to split the data
    """
    return list(chunker(df, chunk_size))



# def being_scan():

# Run the strategy on a single symbol
mt5.initialize()
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD']
# Run the market scanner and execute the strategy on all qualified symbols

def get_symbol(symbol: str) -> pd.DataFrame:
    data = MT5Strategy(
        symbol=symbol,
        lot_size=0.01,
        timeframe=mt5.TIMEFRAME_M5,
        start_time=datetime(2023, 1, 1),
        end_time=datetime(2023, 1, 2)
    )
    return data.fetch_data()

qualified_symbols: List[pd.DataFrame] = [get_symbol(symbol) for symbol in symbols]
strategies = []
for symbol in qualified_symbols:

    item = mt5.symbol_info(symbol.symbol)
    point = item.point
    # print(symbol.symbol, symbol.df.close.iloc[-1], point)
    logger.info(f"{symbol.symbol} {point}")
    run_analysis(symbol.df, point_value=point, show_plot=True)


# logger.info(f"Qualified symbols: {qualified_symbols}")
logger.info(f"number of qualified symbols: {len(qualified_symbols)}")
logger.info(f"qualified_symbols: {qualified_symbols}")
logger.info(f"strategies: {strategies}")
logger.info("starting strategies")
    # loop = asyncio.get_event_loop()

        # for symbol in qualified_symbols:
        #     strategy = MT5Strategy(symbol=symbol, lot_size=0.1, timeframe=mt5.TIMEFRAME_H1, start_time=datetime(2021, 1, 1),
        #                            end_time=datetime.now())
        #     strategies.append(strategy)
        #     # loop.run_until_complete(strategy.run_strategy())
        #     # strategy.run_strategy()
        #
        #
        # #


        # strategy.execute_strategy()

        # strategy = MT5Strategy(symbol="EURUSD", lot_size=0.1, timeframe=mt5.TIMEFRAME_H1, start_time=datetime(2021, 1, 1),

        #                        end_time=datetime.now())

        # strategy.run_strategy()

        # Close MT5 connection
