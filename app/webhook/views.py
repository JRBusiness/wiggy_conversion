"""
Author: Kuro
github: @slapglif
"""
import re
import time
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
        Get symbol info
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
        Close all positions
        """
        mt5_request = None
        if position.type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]:
            info = cls.get_symbol_info(position.symbol)
            # order_request = dict(
            #     action=mt5.TRADE_ACTION_DEAL,
            #     symbol=position.symbol,
            #     volume=position.volume,
            #     price=mt5.ORDER_TYPE_BUY and info.bid or info.ask,
            #     comment=comment,
            #     type=mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            #     time_type=mt5.ORDER_TIME_GTC,
            #     type_filling=mt5.ORDER_FILLING_IOC,
            # )
            mt5.Close(position.symbol)
            # logger.info(f"Order request: {order_request}")
            # mt5_request = mt5.order_send(order_request)

        if mt5_request is None:
            logger.error("Failed to send order request")
            return None

        logger.info(f"Order send result: {mt5_request}")
        if mt5_request.retcode not in [
            mt5.TRADE_RETCODE_REQUOTE,
            mt5.TRADE_RETCODE_PRICE_OFF,
        ] and mt5_request.retcode == mt5.TRADE_RETCODE_DONE:
            return True

    @classmethod
    def close_symbol_trades(cls, request: MT5TradeRequest, open_orders: List[TradePosition]):
        """
        Close symbol trades
        """
        logger.info(f"Attempting to close trades for symbol {request.symbol}")
        for existing_trade in open_orders:
            if existing_trade.type != request.trade_type:
                logger.info(
                    f"Existing trade direction "
                    f"{'buy' if existing_trade.type == mt5.ORDER_TYPE_BUY else 'sell'} "
                    f"is different from the new trade direction {request.trade_type}"
                )
                logger.info(f"Closing trade {existing_trade.ticket}")
                cls.close_all(existing_trade, comment="close and reverse")
                logger.info(
                    f"Order closed: {existing_trade.symbol} "
                    f"at {existing_trade.price_current} "
                    f"using {existing_trade.volume} volume"
                )

    @classmethod
    def get_account(cls):
        """
        Get account info
        """
        account = mt5.account_info()
        logger.debug(f"Account info: {account}")
        balance = account.balance
        logger.debug(f"Account balance: {balance}")
        return account, balance

    @classmethod
    def calculate_volume(cls, symbol, balance: float, price: float) -> float:
        """
        Calculate volume
        """
        symbol_info = mt5.symbol_info(symbol)
        logger.debug(f"Symbol info: {symbol_info}")
        volume = (
            balance / price * 0.002
            if symbol_info.digits == 3
            else balance / price * 0.0002
        )

        if volume < symbol_info.volume_min:
            volume = symbol_info.volume_min
        elif volume > symbol_info.volume_max:
            volume = symbol_info.volume_max

        return round(volume, 2) if volume > 0.01 else 0.01

    @classmethod
    def build_request(cls, trade_data: MT5TradeRequest, price: float, volume: float, trade_type: str  = 'stop') -> dict:
        """
        Build request
        """
        trade_type_data = {}
        if trade_type == 'market':
            trade_type_data = dict(
                action = mt5.TRADE_ACTION_DEAL,
                type = mt5.ORDER_TYPE_BUY if trade_data.trade_type == Actions.BUY else mt5.ORDER_TYPE_SELL,
            )
        elif trade_type == 'stop':
            trade_type_data = dict(
                action = mt5.TRADE_ACTION_PENDING,
                type = mt5.ORDER_TYPE_BUY_STOP if trade_data.trade_type == Actions.BUY else mt5.ORDER_TYPE_SELL_STOP,
            )
        return dict(
            volume=volume,
            symbol=trade_data.symbol,
            price=cls.round_10_cents(price),
            stoplimit=cls.round_10_cents(price + 0.01),
            magic=1337,
            type_filling=mt5.ORDER_FILLING_IOC,
            comment="New position",
        ) | trade_type_data

    @classmethod
    def build_remove_request(cls, trade_data):
        return dict(
            action=mt5.TRADE_ACTION_REMOVE,  # action type
            order=trade_data.ticket,
        )

    @classmethod
    def save_historical_trade(cls, symbol, sent_order):
        """
        Save historical trade
        """
        history = Enumerable(
            mt5.history_deals_get(symbol=symbol)
        ).select(lambda x: TradeDeal(*x)).first_or_default(lambda x: x.ticket == sent_order.order)

        if not history:
            return

        logger.info(f"History: {history}")

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

        trade_history.save()
        return history

    def submit_in_out(self, request: MT5TradeRequest):
        """
        Submit in out
        """
        order_type = 'stop'
        self.open_orders = mt5.positions_get(symbol=request.symbol)
        if existing_trade := Enumerable(self.open_orders).first_or_default(
                lambda x: x.symbol == request.symbol
        ):
            logger.info("Existing trades found")
            if existing_trade.type != (
                    request.trade_type == Actions.BUY and mt5.ORDER_TYPE_BUY
                    or request.trade_type == Actions.SELL and mt5.ORDER_TYPE_SELL
            ):
                logger.info("Closing existing trades and reversing position")
                self.close_symbol_trades(request, [existing_trade])
                order_type = 'market'

            else:
                logger.info("Existing trades are in the same direction as the new trade request. No action needed.")
                return
        else:
            logger.info(f"No open orders found for {request.symbol}")


        if pending_orders := mt5.orders_get(symbol=request.symbol):
            for order in pending_orders:
                pending_request = self.build_remove_request(order)
                logger.info(f"Removing pending order on symbol {order.symbol}")
                mt5.order_send(pending_request)
        open_positions = mt5.positions_get(symbol=request.symbol)
        open_orders = mt5.orders_get(symbol=request.symbol)
        if len(open_positions) + len(open_orders) >= Config.MAX_TRADES:
            logger.error("Maximum number of active trades reached")
            return

        logger.info("Submitting new position")
        return self.submit_trade(request, trade_type=order_type)

    @classmethod
    def round_10_cents(cls, price: float):
        rounded_price = round(price * 100) / 100
        return float("{:.3f}".format(rounded_price))

    @classmethod
    def submit_trade(cls, trade_data: MT5TradeRequest = None, trade_type: str = 'stop'):
        """
        Submit normal
        """
        trade_type == 'stop' and logger.info(f"Attempting to open new trade for symbol {trade_data.symbol}") or \
        logger.info(f"Attempting to close and reverse {trade_data.symbol} at market price")
        account, balance = cls.get_account()
        symbol_data = cls.get_symbol_info(trade_data.symbol)
        price = symbol_data and (
            symbol_data.ask
            if trade_data.trade_type == Actions.BUY
            else symbol_data.bid
        )

        if not balance or not price:
            return

        volume = cls.calculate_volume(trade_data.symbol, balance, price)
        if volume <= 0.1:
            logger.info(f"Volume is negative: {volume}")
            volume = 1.00
        if volume >= 10:
            logger.info(f"Volume is too high: {volume}")
            volume = 1.00
        logger.info(f"Volume: {volume}")

        request = cls.build_request(trade_data, price, volume, trade_type)

        logger.info(f"Executing order: {request}")
        sent_order = mt5.order_send(request)


        if not sent_order:
            _error = mt5.last_error()
            logger.info(f"Failed to send order: {_error}")
            return BaseResponse(error=_error)

        logger.info(f"Order send result: {sent_order}")
        if sent_order.retcode == mt5.TRADE_RETCODE_DONE:
            cls.save_historical_trade(trade_data.symbol, sent_order)
            logger.info("Order saved successfully")
            return sent_order

        logger.info(f"Order {sent_order and request} failed to execute")
        return BaseResponse()


@router.post("/trade_signal", response_model=BaseResponse)
async def receive_trade_signal(webhook_request=Body(...)):
    """
    Receive trade signal
    """
    _tm = TradeManager()
    logger.info(f"Received trade signal: {webhook_request}")

    if isinstance(webhook_request, str):
        return

    item = webhook_request
    item = isinstance(item, (str, dict)) and item or item.decode("utf-8")
    logger.info(f"Received trade signal: {item}")
    if isinstance(item, dict):
        response = MT5TradeRequest.parse_obj(item)
        response.symbol = symbol_map.get(response.symbol, response.symbol)
        _tm.submit_in_out(response)
        return BaseResponse(success=True, response=response)

    item = re.sub(r"(\d+),(\d+)", r"\1\2", item)
    logger.warning(f"Received trade signal: {item}")
    from pydantic import ValidationError

    try:
        obj = MT5TradeRequest.parse_raw(item)
    except ValidationError as e:
        logger.warning("Failed to parse trade signal.")
        logger.debug(f"Error: {e}")
        return BaseResponse(success=False, error="Failed to parse trade signal.")

    response = _tm.submit_in_out(obj)
    logger.warning(obj.symbol, response)

    if response:
        logger.info("Trade signal received and processed successfully.")
        return BaseResponse(
            success=True, response="Trade signal received and processed successfully."
        )

    logger.info("Failed to process trade signal.")
    return BaseResponse(success=False, error="Failed to process trade signal.")
