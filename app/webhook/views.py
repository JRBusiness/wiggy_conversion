from typing import Any

from MetaTrader5 import TradeRequest
from fastapi import FastAPI, HTTPException, APIRouter, Body, params
from fastapi.openapi.models import Schema
from pydantic import BaseModel, BaseConfig
import MetaTrader5 as mt5
from starlette.requests import Request

from app.shared.bases.base_responses import BaseResponse
from app.webhook.schemas import Order, MT5TradeRequest

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


# Function to open a trade in MetaTrader 5
async def open_trade(request: MT5TradeRequest):
    # Open the trade

    order = dict(
        action=mt5.TRADE_ACTION_DEAL,
        symbol=request.symbol,
        volume=request.volume,
        type=mt5.ORDER_TYPE_BUY if request.trade_type == "buy" else mt5.ORDER_TYPE_SELL,
        price=request.entry_price,
        sl=request.stop_loss,
        tp=request.take_profit,
        magic=123456,
        comment="Trade opened from webhook",
        type_time=mt5.ORDER_TIME_GTC,
        type_filling=mt5.ORDER_FILLING_RETURN
    )
    sent_order = mt5.order_send(order)
    mt5.shutdown()
    return sent_order.retcode == mt5.TRADE_RETCODE_DONE

    # order = Order(**request.dict())
    # await order.save()

    # result = mt5.order_send(order.dict())
    # # Check if the trade was opened successfully
    # if result.retcode != mt5.TRADE_RETCODE_DONE:
    #     raise HTTPException(status_code=500, detail="Failed to open trade")


# Endpoint to receive trade signals from the webhook
class RawBody(BaseModel):

    __self__: params.Body

    class Config(BaseConfig):
        json_loads = None




@router.post("/trade_signal", response_model=BaseResponse)
async def receive_trade_signal(webhook_request: MT5TradeRequest): #= Body(media_type="text/plain")):
    # webhook_request = MT5TradeRequest.parse_obj({"symbol": string})
    # Perform necessary validations on the incoming trade signal
    if webhook_request.trade_type not in ["buy", "sell"]:
        return BaseResponse(success=False, error="Invalid trade type. Must be 'buy' or 'sell'.")

    # Process the trade signal and take the appropriate actions (e.g., opening a trade in MetaTrader 5)
    if await open_trade(webhook_request):
        return BaseResponse(success=True, response="Trade signal received and processed successfully.")
    else:
        return BaseResponse(error="Failed to open trade")
