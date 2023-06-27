from datetime import datetime

import pytz
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.shared.bases.base_model import ModelMixin
from app.webhook.schemas import Actions


class Users(ModelMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True)


class Symbols(ModelMixin):
    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tv_symbol = Column(String, nullable=True)
    mt5_symbol = Column(String, nullable=True)
    symbol = Column(String, nullable=True)


class SymbolSettings(ModelMixin):
    __tablename__ = "symbol_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol_id = Column(ForeignKey("symbols.id"), nullable=True)
    symbol = relationship("Symbols", backref="symbol_settings")
    timeframe = Column(String, nullable=True)
    bband_length = Column(Integer, nullable=True)
    bband_stddev = Column(Float, nullable=True)
    wick_pip_threshold = Column(Float, nullable=True)
    ema_length = Column(Integer, nullable=True)
    pip_save_zone = Column(Float, nullable=True)
    max_long_trades = Column(Integer, nullable=True)
    max_short_trades = Column(Integer, nullable=True)
    max_open_trades = Column(Integer, nullable=True)


class TradeHistory(ModelMixin):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=True)
    open_time = Column(DateTime, nullable=True, default=lambda: datetime.now(pytz.utc))
    close_time = Column(DateTime, nullable=True)
    action = Column(String, nullable=True)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    trade_type = Column(String, nullable=True)
    ticket = Column(Integer, nullable=True)
    comment = Column(String, nullable=True)
    magic = Column(Integer, nullable=True)

    @hybrid_property
    def pnl(self):
        return self.exit_price - self.entry_price

    @pnl.expression
    def pnl(cls):
        return cls.exit_price - cls.entry_price

    @hybrid_property
    def profit_loss(self):
        return self.pnl * self.volume

    @profit_loss.expression
    def profit_loss(cls):
        return cls.pnl * cls.volume

    @hybrid_property
    def trade_type(self):
        return Actions

    @trade_type.expression
    def trade_type(cls):
        return "buy" if cls.action == "buy" else "sell"

    @hybrid_property
    def trade_length(self):
        return self.close_time - self.open_time

    @trade_length.expression
    def trade_length(cls):
        return cls.close_time - cls.open_time


class MarketData(ModelMixin):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    timestamp = Column(DateTime)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)


class Signal(ModelMixin):
    __tablename__ = "signal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    timestamp = Column(DateTime)
    signal = Column(String)
    # Include additional columns as needed


class StrategyParams(ModelMixin):
    __tablename__ = "strategy_params"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    bband_length = Column(Integer)
    bband_stddev = Column(Float)
    ema9_length = Column(Integer)
    ema26_length = Column(Integer)
    ema100_length = Column(Integer)
    fibonacci_retrace = Column(Float)


class Strategy(ModelMixin):
    __tablename__ = "strategy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    timestamp = Column(DateTime)
    signal = Column(String)


class Portfolio(ModelMixin):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broker = Column(String)
    leverage = Column(Float)
    balance = Column(Float)
    equity = Column(Float)
    margin = Column(Float)
    free_margin = Column(Float)
    margin_level = Column(Float)
    profit = Column(Float)
    absolute_drawdown = Column(Float)
    minimal_drawdown = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    profit_factor = Column(Float)
    win_rate = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    avg_trade = Column(Float)
    max_consecutive_wins = Column(Integer)
    max_consecutive_losses = Column(Integer)


class StrategyTemplates(ModelMixin):
    __tablename__ = "strategy_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    timeframe = Column(String)
    stategy_id = Column(ForeignKey("strategy.id"), nullable=True)
    strategy = relationship("Strategy", backref="strategy_templates")
    template_name = Column(String)
    params_id = Column(ForeignKey("strategy_params.id"), nullable=True)
    params = relationship("StrategyParams", backref="strategy_templates")
    owner_id = Column(ForeignKey("users.id"), nullable=True)
    owner = relationship("Users", backref="strategy_templates")
