"""
Author: Kuro
github: @slapglif
"""
import re
import time
from enum import Enum
from typing import List

import MetaTrader5 as mt5
from MetaTrader5 import TradeDeal, TradePosition
from fastapi import APIRouter, Body
from loguru import logger
from py_linq import Enumerable
from pydantic import BaseModel

from app.shared.bases.base_responses import BaseResponse
from app.webhook.models import TradeHistory
from app.webhook.schemas import Actions, MT5TradeRequest
from settings import Config

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"],
)

# Initialize MetaTrader 5
mt5.initialize()

# Check if MetaTrader 5 connection is successful
if not mt5.terminal_info():
    error = Exception("Failed to connect to MetaTrader 5 terminal")
    raise error

symbol_map = {
    "US500": "US500Cash",
    "US30": "US30Cash",
    "US100": "US100Cash",
    "JP225": "JP225Cash",
    "USOIL": "OILCash",
}


class OrderType(str, Enum):
    """
    Order type enum
    """
    market: str = "market"
    limit: str = "limit"
    stop: str = "stop"

class TradeManager(BaseModel):
    """
    Trade manager class
    """
    MAX_TRADES: int = Config.MAX_TRADES
    was_closed: bool = False
    open_orders: List[TradePosition] = []

    @classmethod
    def get_symbol_info(cls, symbol: str):
        """
    The get_symbol_info function returns the symbol info for a given symbol.

    Parameters
    ----------
        cls
            Refer to the class itself
        symbol: str
            Pass the symbol to the function

        Returns
        -------

            A symbolinfo object
        """
        try:
            info = mt5.symbol_info(symbol)
            if not info or not info.ask or not info.bid:
                info = mt5.symbol_info_tick(symbol)
            if not info or not info.ask or not info.bid:
                exception =  Exception(f"Failed to get symbol info for {symbol}")
                raise exception
            return info
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")

    @classmethod
    def close_all(cls, position, *, comment=None):
        """
        The close_all function closes all open positions.

        Parameters
        ----------
            cls
                Refer to the class itself
            position
                Identify the position to be closed
            *
                Pass a variable number of arguments to a function
            comment
                Add a comment to the order

        Returns
        -------
            True or false

        """
        mt5_request = None

        # Check if the position is a trade deal
        if position.type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]:
            mt5.Close(position.symbol)

        # Check if the position is a trade position
        if mt5_request is None:
            logger.error("Failed to send order request")
            return None

        # Check if the order request was successful
        logger.info(f"Order send result: {mt5_request}")
        if mt5_request.retcode not in [
            mt5.TRADE_RETCODE_REQUOTE,
            mt5.TRADE_RETCODE_PRICE_OFF,
        ] and mt5_request.retcode == mt5.TRADE_RETCODE_DONE:
            return True

    @classmethod
    def close_symbol_trades(cls, request: MT5TradeRequest, open_orders: List[TradePosition]):
        """
        The close_symbol_trades function is used to close all open trades for a given symbol.
        It takes in the MT5TradeRequest object and a list of TradePosition objects as arguments.
        The function iterates through each TradePosition object in the list, checks if it's direction
        is different from that of the new trade request, and closes it if so.

        Parameters
        ----------
            cls
                Call the close_all function from within the class
            request: MT5TradeRequest
                Pass the trade request to the function
            open_orders: List[TradePosition]
                Pass in the list of open trades for a given symbol

        Returns
        -------
            Nothing
        """
        logger.info(f"Attempting to close trades for symbol {request.symbol}")
        # Iterate through each open trade
        for existing_trade in open_orders:
            # Check if the existing trade direction is different from the new trade direction
            if existing_trade.type != request.trade_type:
                logger.info(
                    f"Existing trade direction "
                    f"{'buy' if existing_trade.type == mt5.ORDER_TYPE_BUY else 'sell'} "
                    f"is different from the new trade direction {request.trade_type}"
                )
                logger.info(f"Closing trade {existing_trade.ticket}")
                # Close the existing trade
                cls.close_all(existing_trade, comment="close and reverse")
                logger.info(
                    f"Order closed: {existing_trade.symbol} "
                    f"at {existing_trade.price_current} "
                    f"using {existing_trade.volume} volume"
                )

    @classmethod
    def get_account(cls):
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
        logger.debug(f"Account info: {account}")
        balance = account.balance
        logger.debug(f"Account balance: {balance}")
        return account, balance

    @classmethod
    def calculate_volume(cls, symbol, balance: float, price: float) -> float:
        """
        The calculate_volume function calculates the volume of a trade based on the balance and price.

        Parameters
        ----------
            cls
                Indicate that the function is a class method
            symbol
                Identify the symbol to be traded
            balance: float
                Specify the amount of money that we want to invest in a trade
            price: float
                Specify the price at which to calculate the volume

        Returns
        -------
            A float

        """
        # Get the symbol info
        symbol_info = mt5.symbol_info(symbol)
        logger.debug(f"Symbol info: {symbol_info}")

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

    @classmethod
    def build_request(cls, trade_data: MT5TradeRequest, price: float, volume: float, trade_type: str  = 'stop') -> dict:
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
                action = mt5.TRADE_ACTION_DEAL,
                type = mt5.ORDER_TYPE_BUY if trade_data.trade_type == Actions.BUY else mt5.ORDER_TYPE_SELL,
                comment="close and reverse",
            )
        elif trade_type == 'stop':
            trade_type_data = dict(
                action = mt5.TRADE_ACTION_PENDING,
                type = mt5.ORDER_TYPE_BUY_STOP if trade_data.trade_type == Actions.BUY else mt5.ORDER_TYPE_SELL_STOP,
                comment="New position",
            )

        # Build the request dictionary and return it
        return dict(
            volume=volume,
            symbol=trade_data.symbol,
            price=cls.round_10_cents(price),
            stoplimit=cls.round_10_cents(price + 0.01),
            magic=1337,
            type_filling=mt5.ORDER_FILLING_IOC,

        ) | trade_type_data

    @classmethod
    def build_remove_request(cls, trade_data):
        """
        The build_remove_request function is used to build a request for removing an order.

        Parameters
        ----------
            cls
                Pass the class name to the function
            trade_data
                Pass the trade data to the function

        Returns
        -------
            A dictionary with the following keys:

        """
        return dict(
                action=mt5.TRADE_ACTION_REMOVE,  # action type
                order=trade_data.ticket,
            )

    @classmethod
    def save_historical_trade(cls, symbol, sent_order):
        """
        The save_historical_trade function saves historical trade data to the database.

        Parameters
        ----------
            cls
                Create a new instance of the class
            symbol
                Get the history of a particular symbol
            sent_order
                Get the order number and comment from the sent_order object

        Returns
        -------
            The history object

        """
        # Get the history of the symbol
        history = Enumerable(
            mt5.history_deals_get(symbol=symbol)
        ).select(lambda x: TradeDeal(*x)).first_or_default(lambda x: x.ticket == sent_order.order)

        # Check if the history is not None and save it to the database
        if not history:
            return

        logger.info(f"History: {history}")

        # Save the history to the database and return it
        trade_history = TradeHistory(
            symbol=symbol,
            entry_price=history.price,
            volume=history.volume,
            trade_type="buy" if history.type == mt5.ORDER_TYPE_BUY else "sell",
            ticket=sent_order.order,
            comment=sent_order.comment,
            magic=sent_order.magic,
            action=Actions.OPEN if TradeManager.was_closed else Actions.CLOSE,
        )

        # Save the trade history to the database
        trade_history.save()
        return history

    def submit_in_out(self, request: MT5TradeRequest):
        """
        The submit_in_out function is used to submit a trade request for the MT5 broker.
        It first checks if there are any existing trades on the symbol in question, and if so, it closes them.
        If there are no open positions or pending orders on that symbol, it submits a new order at market price.

        Parameters
        ----------
            self
                Reference the current instance of a class
            request: MT5TradeRequest
                Pass in the request object to the function

        Returns
        -------

            The result of the submit_trade function

        """

        # Get the symbol info
        order_type = 'stop'
        self.open_orders = mt5.positions_get(symbol=request.symbol)
        # Check if there are any open orders on the symbol
        if existing_trade := Enumerable(self.open_orders).first_or_default(
                lambda x: x.symbol == request.symbol
        ):
            # Check if the existing trade is in the same direction as the new trade request
            logger.info("Existing trades found")
            if existing_trade.type != (
                    request.trade_type == Actions.BUY and mt5.ORDER_TYPE_BUY
                    or request.trade_type == Actions.SELL and mt5.ORDER_TYPE_SELL
            ):
                # If not, close the existing trades and reverse the position
                order_type = OrderType.market
                logger.info("Closing existing trades and reversing position")
                self.close_symbol_trades(request, [existing_trade])

            # If the existing trade is in the same direction as the new trade request, do nothing
            else:
                logger.info("Existing trades are in the same direction as the new trade request. No action needed.")
                return
        else:
            logger.info(f"No open orders found for {request.symbol}")

        # Check if there are any pending orders on the symbol
        if pending_orders := mt5.orders_get(symbol=request.symbol):
            for order in pending_orders:
                # If so, remove them from the symbol
                pending_request = self.build_remove_request(order)
                logger.info(f"Removing pending order on symbol {order.symbol}")
                # Remove the pending order from the symbol
                mt5.order_send(pending_request)

        # Check if there are any open positions on the symbol
        open_positions = mt5.positions_get(symbol=request.symbol)
        open_orders = mt5.orders_get(symbol=request.symbol)

        # Check if the number of open positions and open orders is greater than or equal to the maximum number of trades
        if len(open_positions) + len(open_orders) >= Config.MAX_TRADES:
            logger.error("Maximum number of active trades reached")
            return

        # If not, submit a new order at market price
        order_type == OrderType.market and logger.info("Submitting new position") or logger.info("submitting reverse "
                                                                                                 "order at market")
        # Submit the trade request
        return self.submit_trade(request, trade_type=order_type)

    @classmethod
    def round_10_cents(cls, price: float):
        rounded_price = round(price * 100) / 100
        return float("{:.3f}".format(rounded_price))

    @classmethod
    def submit_trade(cls, trade_data: MT5TradeRequest = None, trade_type: str = 'stop'):
        """
        The submit_trade function is used to submit a trade request to the MetaTrader 5 API.

        Parameters
        ----------
            cls
                Pass the class itself to the function
            trade_data: MT5TradeRequest
                Pass in the trade data
            trade_type: str
                Determine if the trade is a stop loss or not

        Returns
        -------

            A BaseResponse object

        """

        trade_type == 'stop' and logger.info(f"Attempting to open new trade for symbol {trade_data.symbol}") or \
        logger.info(f"Attempting to close and reverse {trade_data.symbol} at market price")
        # Check if the trade data is not None and log the trade data

        account, balance = cls.get_account()
        symbol_data = cls.get_symbol_info(trade_data.symbol)

        # Get the price of the symbol
        price = symbol_data and (
            symbol_data.ask
            if trade_data.trade_type == Actions.BUY
            else symbol_data.bid
        )
        # return if the price is None
        if not balance or not price:
            return

        # Calculate the volume of the trade
        volume = cls.calculate_volume(trade_data.symbol, balance, price)
        if volume <= 0.1:
            logger.info(f"Volume is negative: {volume}")
            volume = 1.00
        if volume >= 10:
            logger.info(f"Volume is too high: {volume}")
            volume = 1.00
        logger.info(f"Volume: {volume}")

        # Build the request object
        request = cls.build_request(trade_data, price, volume, trade_type)

        # Submit the request to the MetaTrader 5 API
        logger.info(f"Executing order: {request}")
        sent_order = mt5.order_send(request)

        # Check if the order was sent successfully and log the result
        if not sent_order:
            _error = mt5.last_error()
            logger.info(f"Failed to send order: {_error}")
            return BaseResponse(error=_error)

        # Check if the order was executed successfully and log the result
        logger.info(f"Order send result: {sent_order}")
        if sent_order.retcode == mt5.TRADE_RETCODE_DONE:
            cls.save_historical_trade(trade_data.symbol, sent_order)
            logger.info("Order saved successfully")
            return sent_order

        # If not, log the result
        logger.info(f"Order {sent_order and request} failed to execute")
        return BaseResponse()


@router.post("/trade_signal", response_model=BaseResponse)
async def receive_trade_signal(webhook_request=Body(...)):
    """
    The receive_trade_signal function receives a trade signal from the MT5 server and processes it.

    Parameters
    ----------
        webhook_request
            Receive the webhook request from mt5

    Returns
    -------

        A BaseResponse object

    """

    # Create a new instance of the TradeManager class
    _tm = TradeManager()
    logger.info(f"Received trade signal: {webhook_request}")

    # Check if the webhook request is a string and return if it is
    if isinstance(webhook_request, str):
        return

    # Check if the webhook request is a dictionary and build the request object
    item = webhook_request
    item = isinstance(item, (str, dict)) and item or item.decode("utf-8")
    logger.info(f"Received trade signal: {item}")
    if isinstance(item, dict):

        # Check if the trade signal is a dictionary and parse it
        response = MT5TradeRequest.parse_obj(item)
        response.symbol = symbol_map.get(response.symbol, response.symbol)

        # Submit the trade signal to the TradeManager class
        _tm.submit_in_out(response)
        return BaseResponse(success=True, response=response)

    # Check if the trade signal is a string and parse it
    item = re.sub(r"(\d+),(\d+)", r"\1\2", item)
    logger.warning(f"Received trade signal: {item}")
    from pydantic import ValidationError

    # Parse the trade signal and log the result of the parsing
    try:
        obj = MT5TradeRequest.parse_raw(item)
    except ValidationError as e:
        logger.warning("Failed to parse trade signal.")
        logger.debug(f"Error: {e}")
        return BaseResponse(success=False, error="Failed to parse trade signal.")

    # Submit the trade signal to the TradeManager class and log the result
    response = _tm.submit_in_out(obj)
    logger.warning(obj.symbol, response)

    # Check if the response is not None and log the result of the trade signal
    if response:
        logger.info("Trade signal received and processed successfully.")
        return BaseResponse(
            success=True, response="Trade signal received and processed successfully."
        )

    # If not, log the result
    logger.info("Failed to process trade signal.")
    return BaseResponse(success=False, error="Failed to process trade signal.")
