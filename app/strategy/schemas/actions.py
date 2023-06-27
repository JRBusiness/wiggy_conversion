from datetime import datetime
from typing import Optional

import MetaTrader5 as mt5
from aredis_om import Field, JsonModel
from pydantic import BaseModel

from app.strategy.schemas.enums import (
    OrderReasonEnum, OrderStateEnum, OrderTypeEnum, OrderTypeFillingEnum, OrderTypeTimeEnum,
    TradeRequestActionsEnum,
)


class Order(JsonModel):
    type_: OrderTypeEnum = Field(..., alias="type")
    state: OrderStateEnum
    reason: OrderReasonEnum

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True

    def send_order(self: "Order"):

        dict(
            action=TradeRequestActionsEnum.deal,
            symbol="EURUSD",
            order_type=self.type_,
            volume=0.1,
            price=1.0,
            sl=0.9,
            tp=1.1,
            magic=12345,
            comment="My Order",

            type_filling=OrderTypeFillingEnum.fok,
            type_time=OrderTypeTimeEnum.gtc,
            type_expiration=OrderTypeTimeEnum.day,
            type_stop=self.type_,
            type_fill=OrderTypeFillingEnum.ioc,
            type_trade=True,
            type_order=True,
            reason=self.reason,
            deviation = 10,
        )



class TradeRequest(JsonModel):
    """
    Hook Order
    """
    symbol: str = Field(default=None, alias="")
    action: str = Field(default=mt5.TRADE_ACTION_DEAL)

    type: int = Field(default=None, alias="")
    type_filling: int = Field(default=None, alias="")

    magic: Optional[int] = Field(default=None, alias="", description="trade grouper / identifier")

    price_open: float = Field(default=None, alias="")
    price_stoplimit: float = Field(default=None, alias="")

    sl: float = Field(default=0.0, alias="")
    tp: float = Field(default=0.0, alias="")

    volume_initial: float = Field(default=None, alias="")


    type_time: Optional[datetime] = Field(default=None, alias="")

    time_expiration: datetime = Field(default=None, alias="")

    comment: Optional[str] = Field(default=None, alias="")
    ticket: Optional[float] = Field(default=None, alias="")

    # Trade deal data
    state: Optional[str] = Field(default=None, alias="")
    external_id: Optional[int] = Field(default=None, alias="")

    position_by_id: Optional[int] = Field(default=None, alias="")
    position_id: Optional[int] = Field(default=None, alias="")

    price_current: Optional[float] = Field(default=None, alias="")
    reason: Optional[str] = Field(default=None, alias="")

    time_done: datetime = Field(default=None, alias="")
    time_done_msc: datetime = Field(default=None, alias="")

    time_setup: datetime = Field(default=None, alias="")
    time_setup_msc: datetime = Field(default=None, alias="")



    volume_current: Optional[float] = Field(default=None, alias="")
