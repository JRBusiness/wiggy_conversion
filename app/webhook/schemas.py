import json
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Union

import MetaTrader5 as mt5
import sentry_sdk
from aredis_om import RedisModel, JsonModel
from fastapi import Body
from pydantic import BaseModel, validator, Field, BaseConfig, Extra
from loguru import logger

logger.debug("Importing schemas from webhook.schemas.py")

sentry_sdk.init()


# Request model for opening a trade in MT5
# class TradeRequest(BaseModel):
#     symbol: str
#     trade_type: str
#     entry_price: float


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


class Context(BaseModel):
    id: int = Field(..., description="ID of the context")
    name: str = Field(..., description="Name of the context")
    description: str = Field(..., description="Description of the context")
    timestamp: datetime = Field(
        ..., description="Date and time of the context creation"
    )
    is_active: bool = Field(..., description="Whether the context is active or not")

    class Config(BaseConfig):
        orm_mode = True


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


class Action(BaseModel):
    action: Actions = Field(..., description="Action to perform on the trade")
    symbol: str = Field(..., description="Symbol to perform the action on")
    trade_id: int = Field(..., description="Trade ID to perform the action on")
    price: float = Field(..., description="Price to perform the action at")
    context: Context = Field(..., description="Context of the action")


class TypeEnum(str, Enum):
    __self__: str

    @classmethod
    def get_type(cls):
        return cls.__self__

    @classmethod
    def get_types(cls):
        return [cls.get_type()]


class TradeTypeEnum(TypeEnum):
    buy: int = mt5.ORDER_TYPE_BUY
    sell: int = mt5.ORDER_TYPE_SELL


class PositionTypeEnum(TypeEnum):
    long: int = mt5.POSITION_TYPE_BUY
    short: int = mt5.POSITION_TYPE_SELL


class OrderTypeEnum(TypeEnum):
    long: str = Actions.BUY
    short: str = Actions.SELL
    buy: int = mt5.ORDER_TYPE_BUY
    sell: int = mt5.ORDER_TYPE_SELL
    buy_limit: int = mt5.ORDER_TYPE_BUY_LIMIT
    sell_limit: int = mt5.ORDER_TYPE_SELL_LIMIT
    buy_stop: int = mt5.ORDER_TYPE_BUY_STOP
    sell_stop: int = mt5.ORDER_TYPE_SELL_STOP
    buy_stop_limit: int = mt5.ORDER_TYPE_BUY_STOP_LIMIT
    sell_stop_limit: int = mt5.ORDER_TYPE_SELL_STOP_LIMIT
    close_by: int = mt5.ORDER_TYPE_CLOSE_BY
    close: int = Actions.CLOSED


class ActionTypeEnum(TypeEnum):
    open: int = mt5.TRADE_ACTION_DEAL
    close: int = mt5.TRADE_ACTION_DEAL
    modify: int = mt5.TRADE_ACTION_MODIFY
    delete: int = mt5.TRADE_ACTION_MODIFY


class AccountTypeEnum(TypeEnum):
    balance: int = mt5.DEAL_TYPE_BALANCE
    credit: int = mt5.DEAL_TYPE_CREDIT


class DealTypeEnum(TypeEnum):
    buy: int = mt5.DEAL_TYPE_BUY
    sell: int = mt5.DEAL_TYPE_SELL
    commission: int = mt5.DEAL_TYPE_COMMISSION
    fee: int = mt5.DEAL_TYPE_COMMISSION
    entry: int = mt5.DEAL_ENTRY_IN
    exit: int = mt5.DEAL_ENTRY_OUT
    inout: int = mt5.DEAL_ENTRY_INOUT


class DealEntryTypeEnum(TypeEnum):
    buy: int = mt5.DEAL_TYPE_BUY
    sell: int = mt5.DEAL_TYPE_SELL
    deposit: int = mt5.DEAL_TYPE_BALANCE
    credit: int = mt5.DEAL_TYPE_CREDIT
    balance: int = mt5.DEAL_TYPE_BALANCE
    commission: int = mt5.DEAL_TYPE_COMMISSION
    fee: int = mt5.DEAL_TYPE_COMMISSION


class Order(JsonModel):
    symbol: str
    volume: float
    trade_type: str
    entry_price: float
    sl: float
    tp: float


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
        logger.debug(f"Value: {value}")
        return round(float(value), 6) if isinstance(value, (float, int)) else value

    """
      Expecting property name enclosed in double quotes: line 1 column 114 (char 113) (type=value_error.jsondecode; msg=Expecting property name enclosed in double quotes; doc={"symbol": "USDCHF",  "trade_type": "buy", "entry_price": 0.9,  "stop_loss":  0,  "take_profit": 0,  "volume": 6,915.4 }; pos=113; lineno=1; colno=114)

    # """
    #
    # @validator("volume", pre=True)
    # def validate_volume(cls, value):
    #     ## in the case of string ploike 234,5545  replace ,
    #     if isinstance(value, str):
    #         value = value.replace(",", "")
    #
    #     logger.debug(f"Value: {value}")
    #
    #     return float(f"{value:.2f}") / 10


class TradeHistoryResponse(BaseModel):
    order: Order


class TradeHistoryRequest(BaseModel):
    start_date: str
    end_date: str
    symbol: Optional[str]
    trade_type: Optional[str]
    entry_price: Optional[float]
    sl: Optional[float] = Field(alias="stop_loss")
    tp: Optional[float] = Field(alias="take_profit")
    volume: Optional[float]
    action: Optional[str]
    order: Optional[Order]


class ToItem(BaseModel):
    address: str
    name: str


class FromItem(BaseModel):
    address: str
    name: str


class Headers(BaseModel):
    received: List[str]
    x_mailsac_inbound_version: str = Field(..., alias='x-mailsac-inbound-version')
    dkim_signature: str = Field(..., alias='dkim-signature')
    x_google_dkim_signature: str = Field(..., alias='x-google-dkim-signature')
    x_gm_message_state: str = Field(..., alias='x-gm-message-state')
    x_google_smtp_source: str = Field(..., alias='x-google-smtp-source')
    x_received: str = Field(..., alias='x-received')
    mime_version: str = Field(..., alias='mime-version')
    from_: str = Field(..., alias='from')
    date: str
    message_id: str = Field(..., alias='message-id')
    subject: str
    to: str
    content_type: str = Field(..., alias='content-type')


class EmailModel(JsonModel):
    _id: Optional[str] = None
    account_id: Optional[str] = Field(None, alias='accountId')
    to: Optional[List[ToItem]] = None
    from_: Optional[List[FromItem]] = Field(None, alias='from')
    subject: Optional[str] = None
    inbox: Optional[str] = None
    original_inbox: Optional[str] = Field(None, alias='originalInbox')
    domain: Optional[str] = None
    received: Optional[str] = None
    raw: Optional[str] = None
    size: Optional[int] = None
    rtls: Optional[bool] = None
    ip: Optional[str] = None
    headers: Optional[Headers] = None
    text: Optional[str] = None
    html: Optional[str] = None
    via: Optional[str] = None
    x_forwarded_for: Optional[str] = Field(None, alias='x-forwarded-for')
