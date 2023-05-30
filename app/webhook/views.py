import json
import re
from _pydecimal import Decimal
from types import SimpleNamespace
from typing import Any, List, Dict, Optional

import MetaTrader5
from MetaTrader5 import TradeRequest, SymbolInfo, TradePosition
from fastapi import FastAPI, HTTPException, APIRouter, Body, params, Depends
from fastapi.openapi.models import Schema
from py_linq import Enumerable
from pydantic import BaseModel, BaseConfig, ValidationError
import MetaTrader5 as mt5
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.requests import Request
from loguru import logger

import settings
from app.shared.bases.base_responses import BaseResponse
from app.webhook.models import TradeHistory
from app.webhook.schemas import Order, MT5TradeRequest, Actions, TradeHistoryRequest

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
    __self__: List["Symbol"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__self__ = self

    def __getitem__(self, item):
        return self.__self__[item]

    def __iter__(self):
        return iter(self.__self__)

    def __len__(self):
        return len(self.__self__)

    def __repr__(self):
        return repr(self.__self__)

    def __str__(self):

        return str(self.__self__)

    def __contains__(self, item):
        return item in self.__self__

    def all(self, symbol: str = None, mt5_symbol: str = None) -> Enumerable:
        if symbol:
            return Enumerable(self.__self__).where(lambda x: x.symbol == symbol)
        elif mt5_symbol:
            return Enumerable(self.__self__).where(lambda x: x.mt5_symbol == mt5_symbol)
        return Enumerable(self.__self__)


class Symbol(BaseModel):
    symbol: Optional[str]
    mt5_symbol: Optional[str]

    class Config:
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
            OILCash="USOIL"
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

    def has_extra_digits(self, symbol):
        """
        Check if the symbol has extra digits in MetaTrader5.
        """
        symbols = mt5.symbols_get()
        return next((s.digits > 5 for s in symbols if s.name == symbol), False)

    def normalize_volume(self, symbol, volume):
        """
        Normalize the volume for order placement in MetaTrader5.
        """
        response = self.has_extra_digits(symbol) and volume * 10 or volume
        return float(f"{response:.2f}")

    async def generate_orders(self, request: MT5TradeRequest):
        open_orders: list[TradePosition] = mt5.positions_get(symbol=request.symbol)
        for existing_trade in open_orders:
            logger.info(f"Existing trade: {existing_trade}")
            # If an existing trade exists, check to see if the direction needs to be changed
            if existing_trade.type != MetaTrader5.ORDER_TYPE_BUY if request.type == Actions.BUY else MetaTrader5.ORDER_TYPE_SELL:
                # If the direction has changed, close all existing trades
                logger.info(
                    f"Existing trade direction "
                    f"{'buy' if existing_trade.type == 1 else 'sell'} "
                    f"is different from the new trade direction {request.type}"
                )

                logger.info(f"Closing trade {existing_trade.ticket}")
                signal = mt5.ORDER_TYPE_BUY if request.type == Actions.BUY else mt5.ORDER_TYPE_SELL

                order = dict(
                    action=mt5.TRADE_ACTION_DEAL,
                    type=signal,
                    volume=self.normalize_volume(request.symbol, request.volume),
                    symbol=existing_trade.symbol,
                    # price=symbol_info.bid if signal == mt5.ORDER_TYPE_BUY else mt5.symbol_info(existing_trade.symbol).ask,
                    position=existing_trade.ticket,
                    order=existing_trade.ticket,
                    deal=existing_trade.ticket,
                    magic=123456,
                    type_filling=mt5.ORDER_FILLING_IOC,
                    comment="closing position from webhook",
                )
                # order['sl'] = existing_trade.price_current
                order_send = mt5.order_send(order)
                logger.info(f"Order send result: {order_send}")
                logger.info(f"Order: {order_send.order}")
                if order_send.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"Order closed: {order_send.order}")
                if order_send.retcode == mt5.TRADE_RETCODE_DONE:
                    trade = TradeHistory(
                        action=Actions.CLOSE,
                        profit=order_send.profit,
                        volume=round(self.normalize_volume(order_send.symbol, order_send.volume), 2),
                        price=order_send.price,
                        symbol=order_send.symbol,
                        type=order_send.type,
                        type_filling=order_send.type_filling,
                        type_time=order_send.type_time,
                        comment=order_send.comment,
                        magic=order_send.magic,
                        order=order_send.order,
                    )

                    trade.save()
                    logger.info(f"Trade history created: {trade}")
                else:
                    logger.info(f"Order close failed: {order_send.retcode}")
                    return

    def new_order(self, trade_data: dict):
        if not (
            last_trade := TradeHistory.where(symbol=trade_data['symbol']).first()
        ):
            return self.order_8(trade_data=trade_data)
        if trade_data['type'] == mt5.ORDER_TYPE_BUY:
            if closed_trade := (last_trade.action == Actions.CLOSE):
                return self.order_8(trade_data, last_trade)

    def order_8(self, trade_data: dict = None, last_trade: int = None):
        trade_data = MT5TradeRequest(**trade_data)
        logger.info(f"Last trade was closed: {last_trade}")

        logger.info("opening new trade")
        registry = Registry()
        order = dict(

            action=mt5.TRADE_ACTION_DEAL,
            type=mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL,
            volume=round(self.normalize_volume(trade_data.symbol, trade_data.volume), 2),
            symbol=trade_data.symbol,
            price=trade_data.entry_price,
            magic=123456,
            type_filling=mt5.ORDER_FILLING_IOC,
            comment="opening position from webhook",
        )

        logger.info(f"Executing order: {order}")
        sent_order = mt5.order_send(order)
        order_ns = SimpleNamespace(**order)
        ticks = mt5.symbol_info_tick(order_ns.symbol)
        current_price = ticks and ticks.bid if order_ns.type == mt5.ORDER_TYPE_BUY else ticks and ticks.ask
        positions = Enumerable(mt5.positions_get())
        if order_ns.symbol == positions.where(
                lambda x: x.symbol == order_ns.symbol
        ).select(
            lambda x: x.symbol
        ):
            self.order_23(positions, order_ns, current_price, sent_order)

        logger.info(f"Order {sent_order and order} executed successfully")

        return sent_order and sent_order.retcode == mt5.TRADE_RETCODE_DONE or BaseResponse()


    def order_23(self, positions, order_ns, current_price, sent_order):
        """
        This method is used to calculate the profit/loss of the order.
        """
        formula = lambda cp, ons: (cp - ons.entry_price) * ons.volume
        pnl = sum(
            formula(current_price, ons) for ons in positions.where(lambda x: x.symbol == order_ns.symbol))
        logger.info(f"Profit/Loss: {pnl}")
        history = TradeHistory(
            symbol=order_ns.symbol,
            open_time=order_ns.open_time,
            close_time=order_ns.close_time,
            entry_price=order_ns.entry_price,
            exit_price=order_ns.exit_price,
            profit=pnl,
            volume=order_ns.volume,
            trade_type="buy" if order_ns.type == mt5.ORDER_TYPE_BUY else "sell",
            ticket=sent_order.order,
            comment=sent_order.comment,
            magic=sent_order.magic,
            action=Actions.OPEN if TradeManager.was_closed else Actions.CLOSE,

        )
        history.save()
        logger.info(f"Trade history created: {history}")

    async def open_trade(self, request: MT5TradeRequest):

        request_data = SimpleNamespace(**request.dict())
        symbol = symbol_map.get(request_data.symbol) or request.symbol
        trade_data = request.dict(exclude_none=True, exclude_unset=True)
        trade_data["symbol"] = symbol

        open_orders = Enumerable(mt5.positions_get()).where(lambda x: x.symbol == symbol)
        account = mt5.account_info()
        balance = account.balance

        logger.info(f"Balance: {balance}")
        logger.info(f"Open orders: {open_orders}")


        symbol_info: SymbolInfo = mt5.symbol_info_tick(symbol)

        bid = (
                symbol_info and self.normalize_volume(
            request_data.symbol,
            symbol_info.bid
        ) or symbol_info and self.normalize_volume(
            request_data.symbol,
            symbol_info.ask
        ) or self.normalize_volume(
            request_data.symbol,
            request_data.entry_price
        )
        )

        new_volume = float(f"{trade_data['volume'] / ((balance * 0.25) / bid):.2f}")

        trade_data['volume]'] = new_volume > 0 and new_volume or float(
            f"{((balance * 0.25) / bid):.2f}") / self.normalize_volume(
            request_data.symbol, request['entry_price'])

        logger.info(f"Trade data: {trade_data}")
        return self.new_order(trade_data)

        # else:
        #     # If the direction is the same, do nothing
        #     logger.info(f"Already a trade open for symbol {request.symbol} and direction {request.trade_type}")
        #     return

    async def get_trade_history(self, request: TradeHistoryRequest):
        # Get the trade history from MetaTrader 5
        # Return the trade history
        pass


#
# @router.get("/symbols_map", response_model=SymbolsMapResponse)
# async def get_symbols_map():
#     symbols: list = mt5.symbols_get()
#     symbols_mapped: Symbols = Symbols.parse_obj(
#         Enumerable(symbols).select(lambda x: Symbol(symbol=x.name, mt5_symbol=x.name)).to_list())
#     return SymbolsMapResponse(response=symbols_mapped)
@router.post("/trade_signal", response_model=BaseResponse)
async def receive_trade_signal(webhook_request=Body(...)):
    logger.info(f"Received trade signal: {webhook_request}")
    tm = TradeManager()
    if isinstance(webhook_request, str):
        return

    item = webhook_request
    item = isinstance(item, (str, dict)) and item or item.decode('utf-8')
    logger.info(f"Received trade signal: {item}")
    if isinstance(item, dict):
        response = MT5TradeRequest.parse_obj(item)
        await tm.open_trade(response)
        return response

    item = re.sub(r'(\d+),(\d+)', r'\1\2', item)
    logger.warning(f"Received trade signal: {item}")
    obj = MT5TradeRequest.parse_raw(item)
    response = await tm.open_trade(obj)

    if response:
        logger.info("Trade signal received and processed successfully.")
        return BaseResponse(success=True, response="Trade signal received and processed successfully.")

    logger.info("Failed to process trade signal.")
    return BaseResponse(success=False, response="Failed to process trade signal.")
