from sqlalchemy_mixins import AllFeaturesMixin
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ModelMixin(AllFeaturesMixin):
    __abstract__ = True


class TradeStats(Base, ModelMixin):
    __tablename__ = "trade_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    profit_loss = Column(Float)

    @hybrid_property
    def win_rate(self):
        # Calculate win rate logic goes here
        return 0.0

    @hybrid_property
    def drawdown(self):
        # Calculate drawdown logic goes here
        return 0.0


class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    open_time = Column(DateTime)
    close_time = Column(DateTime)
    entry_price = Column(Float)
    exit_price = Column(Float)
    profit_loss = Column(Float)


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    timestamp = Column(DateTime)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    # Include additional columns as needed


class OptimizationParams(Base):
    __tablename__ = "optimization_params"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    bband_length = Column(Integer)
    bband_stddev = Column(Float)
    ema9_length = Column(Integer)
    ema26_length = Column(Integer)
    ema100_length = Column(Integer)
    fibonacci_retrace = Column(Float)

    # Include additional columns as needed


class OptimizationStats(Base, ModelMixin):
    __tablename__ = "optimization_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    win_rate = Column(Float)
    drawdown = Column(Float)
    # Include additional columns as needed


class MT5TradeHistory(Base):
    __tablename__ = "mt5_trade_history"

    ticket = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    open_time = Column(DateTime)
    close_time = Column(DateTime)
    entry_price = Column(Float)
    exit_price = Column(Float)
    profit_loss = Column(Float)

    @classmethod
    def from_order_info(cls, order_info: OrderInfo):
        trade = cls()
        trade.ticket = order_info.ticket
        trade.symbol = order_info.symbol
        trade.open_time = order_info.time
        trade.close_time = order_info.time
        trade.entry_price = order_info.price
        trade.exit_price = order_info.price
        trade.profit_loss = order_info.profit
        return trade


# Additional models for MT5 broker-specific data can be added here
