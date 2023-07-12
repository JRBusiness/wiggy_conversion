import asyncio
import json
import sys
from enum import Enum
from typing import List, Optional, Any

import pytz
from MetaTrader5 import TradePosition
from loguru import logger
import MetaTrader5 as mt5
import pandas as pd
from py_linq import Enumerable
from pydantic import BaseModel, BaseConfig, Field, Extra, validator
from datetime import datetime, timedelta

from app.strategy.signal import Signals
from tqdm import tqdm

logger.configure(
    handlers=[
        dict(sink=lambda msg: tqdm.write("", end=""), format="\n{message}"),
        dict(sink="logs/strategy.log", encoding="utf-8", retention="10 days"),
        dict(sink=sys.stdout, level="INFO", backtrace=True, diagnose=True)
    ]

)

class MT5TradeRequest(BaseModel):
    symbol: Optional[str]
    trade_type: Optional[str]
    entry_price: Optional[float] = 0.0
    sl: Optional[float] = Field(alias="stop_loss")
    tp: Optional[float] = Field(alias="take_profit")

    class Config(BaseConfig):
        """
        Config class for the MT5TradeRequest model
        """

        allow_population_by_field_name = True
        extra = Extra.allow
        # create a custom encoder to validate our comma in the volume field and round the float

        class VolumeEncoder(json.JSONEncoder):
            """
            Custom encoder to validate the volume field and round the float
            the volume field needs to be a string with a comma in it, or a float otherwise it will
            just return the value as a rounded float

            """

            def default(self, obj):
                """
                Default method for the custom encoder
                :param obj:
                :return:
                """
                if isinstance(obj, float):
                    return round(obj, 2)
                elif isinstance(obj, str):
                    try:
                        return round(float(obj.replace(",", ".")), 2)
                    except ValueError:
                        return obj
                else:
                    return super().default(obj)

        json_encoders = {
            VolumeEncoder: lambda obj: obj.default(obj),
        }

    #
    @validator("entry_price", "sl", "tp", pre=True)
    def validate_string(cls, value):
        logger.info(f"Value: {value}")
        return round(float(value), 6) if isinstance(value, (float, int)) else value


class Actions(str, Enum):
    OPEN = "open"
    CLOSE = -1
    CLOSED = -1
    MODIFY = "modify"
    STOP = "stop"
    LIMIT = "limit"
    PROFIT = "profit"
    LOSS = "loss"
    CANCEL = "cancel"
    DELETE = "delete"
    UPDATE = "update"
    BUY = "buy"
    SELL = "sell"
    SELL_LIMIT = "sell_limit"
    BUY_LIMIT = "buy_limit"
    SELL_STOP = "sell_stop"
    BUY_STOP = "buy_stop"

    @property
    def all(self):
        return self.get_actions()

    @classmethod
    def get_actions(cls):
        return list(cls.__dict__.keys())

class BaseResponse(BaseModel):
    """
    Base Response abstraction for standardized returns
    """

    success: bool = False
    error: Optional[str] = None
    response: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs) -> dict[str, Any]:
        """
        Override the default dict method to exclude None values in the response
        """
        kwargs.pop("exclude_none", None)
        return super().dict(*args, exclude_none=True, **kwargs)

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
    # timeframe: str = Field(default=None, description="Timeframe to trade")
    # start_time: datetime = Field(default=None, description="Start time of the strategy")
    # end_time: datetime = Field(default=None, description="End time of the strategy")
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

        timeframe = mt5.TIMEFRAME_M1
        timezone = pytz.timezone("Etc/UTC")
        num_candles = 100
        current_time = datetime.now(timezone)
        start_time = current_time - timedelta(minutes=num_candles)
        # logger.info(self.symbol, self.timeframe, start_time)
        candles = []
        for i in range(num_candles):
            current_candle_time = start_time + timedelta(minutes=i)
            flags = mt5.COPY_TICKS_ALL
            ticks = mt5.copy_ticks_range(self.symbol, current_candle_time, current_candle_time + timedelta(minutes=1),
                                         flags)
            if ticks is None or len(ticks) < 2:
                continue
            candle = {
                "time": current_candle_time,
                "open": ticks[0][1],  # Bid price of the first tick
                "high": max(tick[1] for tick in ticks),  # Max bid price of all ticks
                "low": min(tick[1] for tick in ticks),  # Min bid price of all ticks
                "close": ticks[-1][1],  # Bid price of the last tick
                "tick_volume": sum(tick[6] for tick in ticks),  # Sum of tick volumes
                "spread": ticks[0][2] - ticks[0][1],  # Difference between ask and bid price of the first tick
                "real_volume": sum(tick[7] for tick in ticks),  # Sum of real volumes
                # Include other candle attributes as needed
            }
            candles.append(candle)
        df = pd.DataFrame(candles, columns=[
            'time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume', 'spread'
        ])
        df.columns = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume', 'spread']
        df.index = pd.to_datetime(df.index, unit='s')
        df['symbol'] = self.symbol
        logger.info(f"Data fetched for {df['symbol']}")
        return df

    def send_order(self, order_type, price):
        """
        The send_order function sends an order to MT5.

        :param self: Refer to the current instance of a class
        :param order_type: Specify the type of order to be sent
        :param price: Set the price of the order
        :return: A result object
        :doc-author: Trelent
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
        for i, row in self.df.iloc[1:].iterrows():
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



def get_symbol_info(symbol):
    """
    The get_symbol_info function is used to get the current bid and ask prices for a given symbol.
        It first tries to use the mt5.symbol_info function, which returns an object with all of the information about a
        given symbol, including its bid and ask prices. If that fails (which it does sometimes), then it uses
        mt5.symbol_info_tick instead, which only returns an object with information about the last tick for that symbol.

    :param symbol: Specify the symbol you want to get information about
    :return: A dictionary containing the following keys:
    """
    try:
        info = mt5.symbol_info(symbol)
        if not info or not info.ask or not info.bid:
            info = mt5.symbol_info_tick(symbol)
        if not info or not info.ask or not info.bid:
            exception = Exception(f"Failed to get symbol info for {symbol}")
            raise exception
        return info
    except Exception as e:
        logger.error(f"Error getting symbol info: {e}")


class OrderType(str, Enum):
    """
    Order type enum
    """
    market: str = "market"
    limit: str = "limit"
    stop: str = "stop"


def get_symbol(symbol: str) -> pd.DataFrame:
    """
    The get_symbol function fetches the data for a given symbol.

    :param symbol: str: Specify the symbol that we want to get data for
    :return: A pandas dataframe
    """
    data = MT5Strategy(
        symbol=symbol,
    )
    return data.fetch_data()

def get_account():
    """
    The get_account function returns the account info and balance of the current MetaTrader 5 account.

    Parameters
    ----------
        cls
            Pass the class to the function

    Returns
    -------

        A tuple, containing the account info and balance

    """
    account = mt5.account_info()
    logger.info(f"Account info: {account}")
    balance = account.balance
    logger.info(f"Account balance: {balance}")
    return account, balance

def close_all(trade, comment):
    """
    The close_all function is used to close all open trades for a given trade type and symbol.

    Parameters
    ----------
        trade: MT5Trade
            The trade to close
        comment: str
            The comment for the close order

    Returns
    -------
        A BaseResponse object or None

    """
    symbol = trade.symbol
    trade_type = Actions.BUY if trade.type == mt5.ORDER_TYPE_BUY else Actions.SELL
    logger.info(f"Closing all {trade_type} trades for symbol {symbol}")

    # Get the account balance
    _, balance = get_account()

    # Get the symbol data
    symbol_data = get_symbol_info(symbol)

    # Get the price of the symbol
    price = symbol_data and (
        symbol_data.ask
        if trade_type == Actions.BUY
        else symbol_data.bid
    )

    # Return if the price is None
    if not balance or not price:
        return None

    # Calculate the volume of the trade
    volume = trade.volume

    # Build the request object
    request = build_request(symbol, price, volume, trade_type)

    # Submit the request to the MetaTrader 5 API
    logger.info(f"Executing order: {request}")
    sent_order = mt5.order_send(request)

    # Check if the order was sent successfully and log the result
    if sent_order is None:
        _error = mt5.last_error()
        logger.info(f"Failed to send order: {_error}")
        return None

    # Check if the order was executed successfully and log the result
    logger.info(f"Order send result: {sent_order}")
    if sent_order.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info("Order saved successfully")
        return sent_order

    # If not, log the result
    logger.info(f"Order {sent_order and request} failed to execute")
    return None


def close_symbol_trades(trade_type, symbol, open_orders: List[TradePosition]):
    """
    The close_symbol_trades function is used to close all open trades for a given symbol.
    It takes in the trade type (buy or sell) and the symbol as parameters, and then iterates through each open trade.
    If an existing trade direction is different from the new trade direction, it closes that existing order.

    :param trade_type: Determine whether to open a buy or sell trade
    :param symbol: Identify the symbol for which we want to close trades
    :param open_orders: List[TradePosition]: Pass a list of open trades to the function
    :return: A list of closed trades
    """
    logger.info(f"Attempting to close trades for symbol {symbol}")
    # Iterate through each open trade
    for existing_trade in open_orders:
        # Check if the existing trade direction is different from the new trade direction
        if existing_trade.type != trade_type:
            logger.info(
                f"Existing trade direction "
                f"{'buy' if existing_trade.type == mt5.ORDER_TYPE_BUY else 'sell'} "
                f"is different from the new trade direction {trade_type}"
            )
            logger.info(f"Closing trade {existing_trade.ticket}")
            # Close the existing trade
            close_all(existing_trade, comment="close and reverse")
            logger.info(
                f"Order closed: {existing_trade.symbol} "
                f"at {existing_trade.price_current} "
                f"using {existing_trade.volume} volume"
            )

def submit_in_out(symbol, volume, trade_type):
    """
    The submit_in_out function is used to submit a trade request for the symbol.
    It checks if there are any open orders on the symbol, and if so, closes them.
    It also checks if there are any pending orders on the symbol, and removes them.

    :param trade_type: Determine whether the trade is a buy or sell order
    :param symbol: Specify the symbol to trade on
    :return: The order_type
    """
    order_type = 'stop'
    open_orders = mt5.positions_get(symbol=symbol)
    # Check if there are any open orders on the symbol
    if existing_trade := Enumerable(open_orders).first_or_default(
            lambda x: x.symbol == symbol
    ):
        # Check if the existing trade is in the same direction as the new trade request
        logger.info("Existing trades found")
        if existing_trade.type != (
                trade_type == Actions.BUY and mt5.ORDER_TYPE_BUY
                or trade_type == Actions.SELL and mt5.ORDER_TYPE_SELL
        ):
            # If not, close the existing trades and reverse the position
            order_type = OrderType.market
            logger.info("Closing existing trades and reversing position")
            close_symbol_trades(trade_type, symbol, [existing_trade])

        # If the existing trade is in the same direction as the new trade request, do nothing
        else:
            logger.info("Existing trades are in the same direction as the new trade request. No action needed.")
            return
    else:
        logger.info(f"No open orders found for {symbol}")

    # Check if there are any pending orders on the symbol
    if pending_orders := mt5.orders_get(symbol=symbol):
        for order in pending_orders:
            # If so, remove them from the symbol
            pending_request = dict(
                action=mt5.TRADE_ACTION_REMOVE,  # action type
                order=order.ticket,
            )
            logger.info(f"Removing pending order on symbol {order.symbol}")
            # Remove the pending order from the symbol
            mt5.order_send(pending_request)
    return submit_trade(volume, symbol, order_type)


def round_10_cents(price: float):
    rounded_price = round(price * 100) / 100
    return float("{:.3f}".format(rounded_price))


def calculate_volume(symbol, balance: float, price: float) -> float:
    # Get the symbol info
    symbol_info = mt5.symbol_info(symbol)
    logger.info(f"Symbol info: {symbol_info}")

    # Calculate the volume based on the balance and price
    volume = (
        balance / price * 0.002
        if symbol_info.digits == 3
        else balance / price * 0.0002
    )

    # Check if the volume is within the allowed limits
    if volume < symbol_info.volume_min:
        volume = symbol_info.volume_min
    elif volume > symbol_info.volume_max:
        volume = symbol_info.volume_max

    # Return the volume rounded to 2 decimal places
    return round(volume, 2) if volume > 0.01 else 0.01

def build_request(symbol, price: float, volume: float, trade_type: str = 'stop') -> dict:
    """
    The build_request function is used to build a request for the MT5 API.

    Parameters
    ----------
        cls
            Access the class methods
        trade_data: MT5TradeRequest
            Pass the trade data to the function
        price: float
            Set the price of the order
        volume: float
            Specify the volume of the trade
        trade_type: str
            Determine whether the order is a market or stop order

    Returns
    -------
        A dictionary with the following keys:

    """
    #  Build the request based on the trade type (market or stop)
    trade_type_data = {}
    if trade_type == OrderType.market:
        trade_type_data = dict(
            action=mt5.TRADE_ACTION_DEAL,
            type=mt5.ORDER_TYPE_BUY if trade_type == Actions.BUY else mt5.ORDER_TYPE_SELL,
            comment="close and reverse",
        )
    elif trade_type == 'stop':
        trade_type_data = dict(
            action=mt5.TRADE_ACTION_PENDING,
            type=mt5.ORDER_TYPE_BUY_STOP if trade_type == Actions.BUY else mt5.ORDER_TYPE_SELL_STOP,
            comment="New position",
        )

    # Build the request dictionary and return it
    return dict(
        volume=round_10_cents(volume),
        symbol=symbol,
        price=round_10_cents(price),
        stoplimit=round_10_cents(price + 0.01),
        magic=1337,
        type_filling=mt5.ORDER_FILLING_IOC,

    ) | trade_type_data


def submit_trade(volume, symbol, trade_type):
    """
    The submit_trade function is used to submit a trade request to the MetaTrader 5 API.

    Parameters
    ----------
        volume: float
            Specify the volume of the trade
        symbol: str
            The symbol to trade
        trade_type: str
            Determine if the trade is a stop loss or not

    Returns
    -------
        A BaseResponse object or None

    """

    trade_type == 'stop' and logger.info(f"Attempting to open new trade for symbol {symbol}") or \
    logger.info(f"Attempting to close and reverse {symbol} at market price")
    # Check if the trade data is not None and log the trade data

    _, balance = get_account()
    symbol_data = get_symbol_info(symbol)

    # Get the price of the symbol
    price = symbol_data and (
        symbol_data.ask
        if trade_type == 'buy'
        else symbol_data.bid
    )
    # return if the price is None
    if not balance or not price:
        return None

    # Calculate the volume of the trade
    if volume <= 0.1:
        logger.info(f"Volume is negative: {volume}")
        volume = 1.00
    if volume >= 10:
        logger.info(f"Volume is too high: {volume}")
        volume = 1.00
    logger.info(f"Volume: {volume}")

    # Build the request object
    request = build_request(symbol, price, volume, trade_type)

    # Submit the request to the MetaTrader 5 API
    logger.info(f"Executing order: {request}")
    sent_order = mt5.order_send(request)

    # Check if the order was sent successfully and log the result
    if sent_order is None:
        _error = mt5.last_error()
        logger.info(f"Failed to send order: {_error}")
        return None

    # Check if the order was executed successfully and log the result
    logger.info(f"Order send result: {sent_order}")
    if sent_order.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info("Order saved successfully")
        return sent_order

    # If not, log the result
    logger.info(f"Order {sent_order and request} failed to execute")
    return None


mt5.initialize()
symbols = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD',
    "BTCUSD", "ETHUSD", "LTCUSD", "BCHUSD",
    "BATUSD", "XRPUSD", "COMPUSD", "STORJUSD",
    "AAVEUSD", "SOLUSD", "SNXUSD", "SKLUSD"
]

# while True:
for symbol in symbols:
    signal = Signals()
    signal = signal.check_signal(symbol, show_plot=True)
    if signal:
        account_info = mt5.account_info()
        margin = account_info.margin
        available_margin = account_info.equity - margin
        volume = calculate_volume(symbol, available_margin, signal.get("entry_price"))
        submit_in_out(symbol, volume, signal.get("trade_type"))
        # time.sleep(60)
