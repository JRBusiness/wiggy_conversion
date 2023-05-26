from typing import Optional

from aredis_om import RedisModel, JsonModel
from fastapi import Body
from pydantic import BaseModel, validator


# Request model for opening a trade in MT5
class TradeRequest(BaseModel):
    symbol: str
    trade_type: str
    entry_price: float


class WebhookRequest(BaseModel):
    signal: str
    symbol: str
    trade_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float


# Response model for the trade operation in MT5
class TradeResponse(BaseModel):
    trade_id: int
    symbol: str
    trade_type: str
    entry_price: float

# Request model for retrieving trade statistics in a given time window
class TradeStatsRequest(BaseModel):
    start_date: str
    end_date: str

# Response model for trade statistics
class TradeStatsResponse(BaseModel):
    total_trades: int
    total_profit: float
    total_loss: float
    win_rate: float

class Order(JsonModel):
    symbol: str
    volume: float
    type: str
    price: float
    sl: float
    tp: float
#
# class TradeData(BaseModel):
#     symbol: str
#     trade_type: str
#     entry_price: float
#     stop_loss: float
#     take_profit: float
#     volume: float
#
#     @validator('symbol', 'trade_type', 'entry_price', 'stop_loss', 'take_profit', 'volume')
#     def extract_values(cls, value):
#         strategy_params = value.split(', ')
#         symbol = strategy_params[0].split(' ')[-1]
#         trade_type = strategy_params[1].split(' ')[-1]
#         entry_price = float(strategy_params[2])
#         stop_loss = float(strategy_params[3])
#         take_profit = float(strategy_params[4])
#         volume = float(strategy_params[9])
#
#         return {
#             'symbol': symbol,
#             'trade_type': trade_type,
#             'entry_price': entry_price,
#             'stop_loss': stop_loss,
#             'take_profit': take_profit,
#             'volume': volume
#         }


class MT5TradeRequest(BaseModel):
    symbol: str
    trade_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float

    # @validator('symbol', 'trade_type', 'entry_price', 'stop_loss', 'take_profit', 'volume')
    # def extract_values(cls, value):
    #     strategy_params = value.split(', ')
    #     symbol = strategy_params[0].split(' ')[-1]
    #     trade_type = strategy_params[1].split(' ')[-1]
    #     entry_price = float(strategy_params[2])
    #     stop_loss = float(strategy_params[3])
    #     take_profit = float(strategy_params[4])
    #     volume = float(strategy_params[9])
    #
    #     return {
    #         'symbol': symbol,
    #         'trade_type': trade_type,
    #         'entry_price': entry_price,
    #         'stop_loss': stop_loss,
    #         'take_profit': take_profit,
    #         'volume': volume
    #     }