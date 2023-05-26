from typing import Optional

from pydantic import BaseModel, Field
from redis_om import RedisModel


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

class MT5TradeRequest(BaseModel):
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

class Order(RedisModel):
    action: str
    symbol: str
    volume: float
    type: str
    price: float
    sl: float
    tp: float
    magic: Optional[int]
    comment: Optional[str]
    type_time: Optional[str]
    type_filling: Optional[str]
