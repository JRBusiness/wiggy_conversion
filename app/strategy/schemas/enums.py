from enum import Enum


class ENUM_POSITION_TYPE(Enum):
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

class ENUM_POSITION_REASON(Enum):
    POSITION_REASON_CLIENT = 0
    POSITION_REASON_MOBILE = 1
    POSITION_REASON_WEB = 2
    POSITION_REASON_EXPERT = 3

class ENUM_ORDER_TYPE(Enum):
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7
    ORDER_TYPE_CLOSE_BY = 8

class ENUM_ORDER_STATE(Enum):
    ORDER_STATE_STARTED = 0
    ORDER_STATE_PLACED = 1
    ORDER_STATE_CANCELED = 2
    ORDER_STATE_PARTIAL = 3
    ORDER_STATE_FILLED = 4
    ORDER_STATE_REJECTED = 5
    ORDER_STATE_EXPIRED = 6
    ORDER_STATE_REQUEST_ADD = 7
    ORDER_STATE_REQUEST_MODIFY = 8
    ORDER_STATE_REQUEST_CANCEL = 9

class ENUM_ORDER_TYPE_FILLING(Enum):
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    ORDER_FILLING_BOC = 3

class ENUM_ORDER_TYPE_TIME(Enum):
    ORDER_TIME_GTC = 0
    ORDER_TIME_DAY = 1
    ORDER_TIME_SPECIFIED = 2
    ORDER_TIME_SPECIFIED_DAY = 3

class ENUM_ORDER_REASON(Enum):
    ORDER_REASON_CLIENT = 0
    ORDER_REASON_MOBILE = 1
    ORDER_REASON_WEB = 2
    ORDER_REASON_EXPERT = 3
    ORDER_REASON_SL = 4
    ORDER_REASON_TP = 5
    ORDER_REASON_SO = 6

class ENUM_DEAL_TYPE(Enum):
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_TYPE_BALANCE = 2
    DEAL_TYPE_CREDIT = 3
    DEAL_TYPE_CHARGE = 4
    DEAL_TYPE_CORRECTION = 5
    DEAL_TYPE_BONUS = 6
    DEAL_TYPE_COMMISSION = 7
    DEAL_TYPE_COMMISSION_DAILY = 8
    DEAL_TYPE_COMMISSION_MONTHLY = 9
    DEAL_TYPE_COMMISSION_AGENT_DAILY = 10
    DEAL_TYPE_COMMISSION_AGENT_MONTHLY = 11
    DEAL_TYPE_INTEREST = 12
    DEAL_TYPE_BUY_CANCELED = 13
    DEAL_TYPE_SELL_CANCELED = 14
    DEAL_DIVIDEND = 15
    DEAL_DIVIDEND_FRANKED = 16
    DEAL_TAX = 17

class ENUM_DEAL_ENTRY(Enum):
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_ENTRY_INOUT = 2
    DEAL_ENTRY_OUT_BY = 3

class ENUM_DEAL_REASON(Enum):
    DEAL_REASON_CLIENT = 0
    DEAL_REASON_MOBILE = 1
    DEAL_REASON_WEB = 2
    DEAL_REASON_EXPERT = 3
    DEAL_REASON_SL = 4
    DEAL_REASON_TP = 5
    DEAL_REASON_SO = 6
    DEAL_REASON_ROLLOVER = 7
    DEAL_REASON_VMARGIN = 8
    DEAL_REASON_SPLIT = 9

class ENUM_TRADE_REQUEST_ACTIONS(Enum):
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    TRADE_ACTION_SLTP = 6
    TRADE_ACTION_MODIFY = 7
    TRADE_ACTION_REMOVE = 8
    TRADE_ACTION_CLOSE_BY = 10


from enum import Enum
from pydantic import BaseModel, Field

class PositionTypeEnum(str, Enum):
    buy = "POSITION_TYPE_BUY"
    sell = "POSITION_TYPE_SELL"

class PositionReasonEnum(str, Enum):
    client = "POSITION_REASON_CLIENT"
    mobile = "POSITION_REASON_MOBILE"
    web = "POSITION_REASON_WEB"
    expert = "POSITION_REASON_EXPERT"

class OrderTypeEnum(str, Enum):
    buy = "ORDER_TYPE_BUY"
    sell = "ORDER_TYPE_SELL"
    buy_limit = "ORDER_TYPE_BUY_LIMIT"
    sell_limit = "ORDER_TYPE_SELL_LIMIT"
    buy_stop = "ORDER_TYPE_BUY_STOP"
    sell_stop = "ORDER_TYPE_SELL_STOP"
    buy_stop_limit = "ORDER_TYPE_BUY_STOP_LIMIT"
    sell_stop_limit = "ORDER_TYPE_SELL_STOP_LIMIT"
    close_by = "ORDER_TYPE_CLOSE_BY"

class OrderStateEnum(str, Enum):
    started = "ORDER_STATE_STARTED"
    placed = "ORDER_STATE_PLACED"
    canceled = "ORDER_STATE_CANCELED"
    partial = "ORDER_STATE_PARTIAL"
    filled = "ORDER_STATE_FILLED"
    rejected = "ORDER_STATE_REJECTED"
    expired = "ORDER_STATE_EXPIRED"
    request_add = "ORDER_STATE_REQUEST_ADD"
    request_modify = "ORDER_STATE_REQUEST_MODIFY"
    request_cancel = "ORDER_STATE_REQUEST_CANCEL"

class OrderTypeFillingEnum(str, Enum):
    fok = "ORDER_FILLING_FOK"
    ioc = "ORDER_FILLING_IOC"
    _return = "ORDER_FILLING_RETURN"
    boc = "ORDER_FILLING_BOC"

class OrderTypeTimeEnum(str, Enum):
    gtc = "ORDER_TIME_GTC"
    day = "ORDER_TIME_DAY"
    specified = "ORDER_TIME_SPECIFIED"
    specified_day = "ORDER_TIME_SPECIFIED_DAY"

class OrderReasonEnum(str, Enum):
    client = "ORDER_REASON_CLIENT"
    mobile = "ORDER_REASON_MOBILE"
    web = "ORDER_REASON_WEB"
    expert = "ORDER_REASON_EXPERT"
    sl = "ORDER_REASON_SL"
    tp = "ORDER_REASON_TP"
    so = "ORDER_REASON_SO"

class DealTypeEnum(str, Enum):
    buy = "DEAL_TYPE_BUY"
    sell = "DEAL_TYPE_SELL"
    balance = "DEAL_TYPE_BALANCE"
    credit = "DEAL_TYPE_CREDIT"
    charge = "DEAL_TYPE_CHARGE"
    correction = "DEAL_TYPE_CORRECTION"
    bonus = "DEAL_TYPE_BONUS"
    commission = "DEAL_TYPE_COMMISSION"
    commission_daily = "DEAL_TYPE_COMMISSION_DAILY"
    commission_monthly = "DEAL_TYPE_COMMISSION_MONTHLY"
    commission_agent_daily = "DEAL_TYPE_COMMISSION_AGENT_DAILY"
    commission_agent_monthly = "DEAL_TYPE_COMMISSION_AGENT_MONTHLY"
    interest = "DEAL_TYPE_INTEREST"
    buy_canceled = "DEAL_TYPE_BUY_CANCELED"
    sell_canceled = "DEAL_TYPE_SELL_CANCELED"
    dividend = "DEAL_DIVIDEND"
    dividend_franked = "DEAL_DIVIDEND_FRANKED"
    tax = "DEAL_TAX"

class DealEntryEnum(str, Enum):
    entry_in = "DEAL_ENTRY_IN"
    entry_out = "DEAL_ENTRY_OUT"
    entry_inout = "DEAL_ENTRY_INOUT"
    entry_out_by = "DEAL_ENTRY_OUT_BY"

class DealReasonEnum(str, Enum):
    client = "DEAL_REASON_CLIENT"
    mobile = "DEAL_REASON_MOBILE"
    web = "DEAL_REASON_WEB"
    expert = "DEAL_REASON_EXPERT"
    sl = "DEAL_REASON_SL"
    tp = "DEAL_REASON_TP"
    so = "DEAL_REASON_SO"
    rollover = "DEAL_REASON_ROLLOVER"
    vmargin = "DEAL_REASON_VMARGIN"
    split = "DEAL_REASON_SPLIT"

class TradeRequestActionsEnum(str, Enum):
    deal = "TRADE_ACTION_DEAL"
    pending = "TRADE_ACTION_PENDING"
    sltp = "TRADE_ACTION_SLTP"
    modify = "TRADE_ACTION_MODIFY"
    remove = "TRADE_ACTION_REMOVE"
    close_by = "TRADE_ACTION_CLOSE_BY"

class Position(BaseModel):
    type_: PositionTypeEnum = Field(..., alias="type")
    reason: PositionReasonEnum

    class Config:
        use_enum_values = True



class Deal(BaseModel):
    type_: DealTypeEnum