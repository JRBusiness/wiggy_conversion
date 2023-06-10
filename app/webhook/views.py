# sourcery skip: raise-specific-error
"""
This module contains the webhook views
"""
import requests
from bs4 import BeautifulSoup
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional, Any

import MetaTrader5 as mt5
import pytz
from MetaTrader5 import TradePosition
from fastapi import APIRouter, Body
from loguru import logger
from py_linq import Enumerable
from pydantic import BaseModel
from starlette.requests import Request

from app.shared.bases.base_responses import BaseResponse
from app.strategy.lookup_schemas import SignatureModel, EmailModel, parse_email, Email
from app.webhook.models import TradeHistory
from app.webhook.schemas import Order, MT5TradeRequest, Actions
from settings import Config

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"],
)
# Webhook Request Model


# Initialize MetaTrader 5
mt5.initialize()

# Check if MetaTrader 5 connection is successful
if not mt5.terminal_info():
    raise Exception("Failed to connect to MetaTrader 5 terminal")


class Symbols(BaseModel):
    __abstract__ = True
    __self__: List["Symbol"]

    def __init__(self):
        super().__init__()

    def __contains__(self, item):
        return item in self.__self__

    def all(self, symbol: str = None, mt5_symbol: str = None) -> Enumerable:
        """
        Get all symbols
        :param symbol:
        :param mt5_symbol:
        :return:
        """
        if symbol:
            return Enumerable(self.__self__).where(lambda x: x.symbol == symbol)
        elif mt5_symbol:
            return Enumerable(self.__self__).where(lambda x: x.mt5_symbol == mt5_symbol)
        return Enumerable(self.__self__)


class Symbol(BaseModel):
    symbol: Optional[str]
    mt5_symbol: Optional[str]

    class Config:
        """
        Pydantic configuration
        """

        orm_mode = True

    @staticmethod
    def init_symbols_map(default_symbols: Optional[Dict[str, str]] = None) -> Symbols:
        """
        Initialize the symbols map.
        :return: List of symbols
        """
        base = default_symbols or dict(
            US500Cash="US500",
            US30Cash="US30",
            US100Cash="US100",
            JP225Cash="JP225",
            OILCash="USOIL",
        )

        symbols = mt5.symbols_get()
        Symbols.update_forward_refs()
        data = [
            Symbol(symbol=base.get(symbol.name), mt5_symbol=symbol.name)
            for symbol in symbols
        ]
        return Symbols.construct(__self__=data)


class Registry(BaseModel):
    symbols: Optional[List[Symbol]] = Symbol.init_symbols_map()
    orders: Optional[List[Order]]
    positions: Optional[List[TradePosition]]
    choices: Optional[List[Actions]]


class SymbolsMapResponse(BaseResponse):
    response: Symbols

    class Config:
        """
        Pydantic configuration
        """

        orm_mode = True


symbol_map = {
    "US500": "US500Cash",
    "US30": "US30Cash",
    "US100": "US100Cash",
    "JP225": "JP225Cash",
    "USOIL": "OILCash",
}


class TradeManager(BaseModel):
    was_closed: bool = False

    open_orders: List[TradePosition] = []

    def close_trades(self, request: MT5TradeRequest, open_orders: List[TradePosition]):
        """ "
        Close all open trades

        """
        for existing_trade in open_orders:
            logger.info(f"Existing trade: {existing_trade}")
            # If an existing trade exists, check to see if the direction needs to be changed
            if existing_trade.type != (
                request.trade_type == Actions.BUY
                and mt5.ORDER_TYPE_BUY
                or request.trade_type == Actions.SELL
                and mt5.ORDER_TYPE_SELL
            ):
                # If the direction has changed, close all existing trades
                logger.info(
                    f"Existing trade direction "
                    f"{'buy' if existing_trade.type == 0 else 'sell'} "
                    f"is different from the new trade direction {request.trade_type}"
                )
                logger.info(f"Closing trade {existing_trade.ticket}")
                order_sent = mt5.Close(
                    existing_trade.symbol,
                    ticket=existing_trade.ticket,
                    comment="close and reverse",
                )
                logger.info(f"Order send result: {order_sent}")
                if order_sent:
                    logger.info(
                        f"Order closed: {existing_trade.symbol} "
                        f"at {existing_trade.price_current} "
                        f"using {existing_trade.volume} volume"
                    )

    async def submit_in_out(self, request: MT5TradeRequest):
        """
        Submit an in/out trade request
        :param request:
        :return:
        """
        open_orders: list[TradePosition] = mt5.positions_get(symbol=request.symbol)
        logger.info(f"Open orders: {open_orders}")

        if not open_orders:
            logger.info("No open orders found")
            self.submit_normal(request)
            return

        self.close_trades(request, open_orders)

        logger.info("submitting reverse position")
        self.submit_normal(request)

    @classmethod
    def get_prices(cls, trade_data: MT5TradeRequest, factor: float = 0.01):
        """
        The get_prices function is used to get the current price of a symbol, as well as the stop loss and take profit prices.
        The function takes in a trade_data object which contains information about the trade such as symbol, type (buy/sell), etc.
        It also takes in an optional factor parameter that defaults to 0.01 which is used for calculating volume based on account balance.

        Args:
            cls: Represent the instance of the class
            trade_data: MT5TradeRequest: Get the symbol and trade type from the mt5 trade request class
            factor: float: Determine the percentage of the account balance to use for each trade

        Returns:
            A tuple of three values:

        """
        account = mt5.account_info()
        balance = account.balance
        symbol_data = mt5.symbol_info(trade_data.symbol)
        price = (
            symbol_data.ask if trade_data.trade_type == Actions.BUY else symbol_data.bid
        )
        volume = balance / price * factor
        return price, (price - 100), (price + 100), volume

    def submit_normal(self, trade_data: MT5TradeRequest = None):
        """
        Submit an in/out order.
        """
        logger.info("opening new trade")
        account = mt5.account_info()
        balance = account.balance
        symbol_data = mt5.symbol_info(trade_data.symbol)
        price = symbol_data and (
            symbol_data.ask if trade_data.trade_type == Actions.BUY else symbol_data.bid
        )
        if not balance or not price:
            return
        volume = float(f"{balance / price * 0.02:.2f}")
        # check if the current symbol is one of the ones with an additional digit
        # componssate by setting the volume lower for that symbols trades
        #
        # first we must get the  current symbols digits from the broker
        symbol = mt5.symbol_info(trade_data.symbol)
        if symbol.digits == 3:
            volume = float(f"{balance / price * 0.002:.2f}")
        elif symbol.digits == 5:
            volume = float(f"{balance / price * 0.0002:.2f}")
        logger.info(f"Volume: {volume}")
        trade_data.volume = volume

        order = dict(
            action=mt5.TRADE_ACTION_DEAL,
            type=mt5.ORDER_TYPE_BUY
            if trade_data.trade_type == Actions.BUY
            else mt5.ORDER_TYPE_SELL,
            volume=trade_data.volume,
            symbol=trade_data.symbol,
            price=trade_data.entry_price,
            magic=123456,
            type_filling=mt5.ORDER_FILLING_IOC,
            comment="Entry no Close",
        )

        logger.info(f"Executing order: {order}")
        sent_order = mt5.order_send(order)
        if not sent_order:
            logger.info(f"failed  send result: {sent_order}")
            return
        logger.info(f"Order send result: {sent_order}")
        if sent_order.retcode == mt5.TRADE_RETCODE_DONE:
            #     self.save_historical_trade(trade_data.symbol, sent_order.price, sent_order)
            #     logger.info(f"Order {sent_order and order} executed successfully")
            return (
                sent_order
                and sent_order.retcode == mt5.TRADE_RETCODE_DONE
                or BaseResponse()
            )

        logger.info(f"Order {sent_order and order} failed to execute")
        return BaseResponse

    @classmethod
    def save_historical_trade(cls, symbol, closed_deal, sent_order):
        """
        This method is used to calculate the profit/loss of the order.
        """
        history = TradeHistory(
            symbol=symbol,
            open_time=lambda x: datetime.now(pytz.utc),
            close_time=None,
            entry_price=closed_deal.entry_price,
            exit_price=closed_deal.exit_price,
            volume=closed_deal.volume,
            trade_type="buy" if closed_deal.type == mt5.ORDER_TYPE_BUY else "sell",
            ticket=sent_order.order,
            comment=sent_order.comment,
            magic=sent_order.magic,
            action=Actions.OPEN if TradeManager.was_closed else Actions.CLOSE,
        )
        history.save()
        logger.info(f"Trade history created: {history}")
        return history


@router.post("/trade_signal", response_model=BaseResponse)
async def receive_trade_signal(webhook_request=Body(...)):
    """
    Receive trade signal from the webhook
    :param webhook_request:
    :return:
    """
    tm = TradeManager()
    logger.info(f"Received trade signal: {webhook_request}")

    if isinstance(webhook_request, str):
        return

    item = webhook_request
    item = isinstance(item, (str, dict)) and item or item.decode("utf-8")
    logger.info(f"Received trade signal: {item}")
    if isinstance(item, dict):
        response = MT5TradeRequest.parse_obj(item)
        await tm.submit_in_out(response)
        return response

    item = re.sub(r"(\d+),(\d+)", r"\1\2", item)
    logger.warning(f"Received trade signal: {item}")
    obj = MT5TradeRequest.parse_raw(item)
    response = await tm.submit_in_out(obj)
    logger.warning(obj.symbol, response)

    if response:
        logger.info("Trade signal received and processed successfully.")
        return BaseResponse(
            success=True, response="Trade signal received and processed successfully."
        )

    logger.info("Failed to process trade signal.")
    return BaseResponse(response="Failed to process trade signal.")


# @router.post("/test")
# async def test_webhook(request: Request):
#     # print(request.json())
#
#     body = await request.json()
#     data = SignatureModel(**body)
#     logger.info(data)
#     session = requests.Session()
#     session.headers.update({"Accept": "message/rfc2822"})
#     session.params = dict({"limit": "10"})
#     url = data.event_data.storage.url
#     request = session.get(
#         url,
#         auth=("api", Config.api_key),
#     )
#     email_main = EmailModel(**request.json())
#     logger.info(email_main)
#
#     response: Email = parse_email(email_main.body_mime)
#
#     return BaseResponse(success=True, response=response.code)
