from datetime import datetime
from types import SimpleNamespace
from typing import List, Dict
import backtrader as bt
import numpy as np
import pandas as pd
from backtrader import Strategy, Order
from numpy import fmin
from scipy.constants import hp

import settings


from models import calculate_sharpe_ratio, calculate_max_drawdown, calculate_sortino_ratio
from rules import RuleFilter, calculate_quantity, data



# from matplotlib import plt
# from alpaca_trade_api import AsyncRest
#
# client = AsyncRest(
#     key_id=settings.Config.alpaca_key,
#     secret_key=settings.Config.alpaca_secret,
#     data_url=settings.Config.alpaca_base_url
# )


class BacktestingStrategy(bt.Strategy):
    """
    The BacktestingStrategy class is used to backtest a trading strategy.
    """
    params = (
        ('entry_rules', []),
        ('exit_rules', []),
        ('reverse_rules', [])
    )

    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the parameters and other things needed for this strategy to work.


        Args:
            self: Represent the instance of the class

        Returns:
            The entry_filters, exit_filters, and reverse_filters
        """
        self.entry_filters = []
        self.exit_filters = []
        self.reverse_filters = []

        self.entry_filters.extend(RuleFilter(rule) for rule in self.params.entry_rules)
        self.exit_filters.extend(RuleFilter(rule) for rule in self.params.exit_rules)
        self.reverse_filters.extend(
            RuleFilter(rule) for rule in self.params.reverse_rules
        )

    def next(self):
        """
        The next function is called by the backtrader framework to calculate
        the next bar.  It will be called for every bar in the data feed, so it's
        important that we only execute our trading logic when we have enough data.
        The first time this function is called, there are no bars in self.datas[0],
        so we return immediately without doing anything.

        Args:
            self: Represent the instance of the class

        Returns:
            The next function of the strategy, which is a function that checks if the entry conditions are met

        """
        if not self.position:
            for _filter in self.entry_filters:
                if not _filter.check(self.datas[0]):
                    return
            self.buy()
        else:
            for _filter in self.exit_filters:
                if not _filter.check(self.datas[0]):
                    return
            self.close()
            for _filter in self.reverse_filters:
                if not _filter.check(self.datas[0]):
                    return
            self.reverse_position()

    def reverse_position(self):
        """
        The reverse_position function is used to reverse the
        position of a stock.
        It does this by first selling all shares, then
        buying back the same amount of shares.

        Args:
            self: Refer to the object itself
        """
        self.sell()
        self.buy()


class BacktestingEngine:
    """
    The BacktestingEngine class is used to backtest a strategy.
    """

    def __init__(self, strategy, data, start_date, end_date, initial_capital):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the strategy, data, start and end dates, and initial
        capital for backtesting.

        Args:
            self: Represent the instance of the class
            strategy: Pass in the strategy class that we want to use
            data: Pass the data to the strategy
            start_date: Set the start date of the backtest
            end_date: Set the end date of the backtest
            initial_capital: Set the initial capital of the broker

        Returns:
            An instance of the class
        """
        self.performance_stats = None
        self.strategy = strategy
        self.data = data
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        self.cerebro = bt.Cerebro()
        self.cerebro.addstrategy(self.strategy)
        self.cerebro.adddata(self.data)
        self.cerebro.broker.set_cash(self.initial_capital)

    def run_backtest(self):
        """
        The run_backtest function is the main function that runs the backtest.
        It takes no arguments and returns nothing. It simply calls cerebro's run() method,
        which in turn calls our strategy's next() method for each bar of data.

        Args:
            self: Represent the instance of the class

        Returns:
            A dictionary of performance statistics
        """
        self.cerebro.run()
        self.performance_stats = self.calculate_performance_stats()

    def calculate_performance_stats(self):
        """
        The calculate_performance_stats function takes a list of trades and returns a dictionary with the following keys:
            - total_profit: The sum of all profits from closed trades.
            - total_losses: The sum of all losses from closed trades.
            - profit_factor: (total_profit / abs(total_losses)) if there are any losses, otherwise None.
            - winrate: Percentage of winning trades out of the total number of closed trades, or None if no trade was made yet.

        Args:
            self: Access the attributes and methods of a class

        Returns:
            A dictionary with the following keys:


        """
        trades = [
            Trade.from_backtrader_trade(trade)
            for _, trade in self.cerebro.trades.get_analysis().items()
        ]
        return calculate_performance_stats(trades)

    def visualize_results(self):
        """
        The visualize_results function is used to plot the results of a backtest.
        It plots the equity curve, and also prints out some performance statistics.

        Args:
            self: Bind the method to an object

        Returns:
            A plot of the strategy and performance statistics
        """
        self.cerebro.plot()
        self.performance_stats.plot()


class Trade:
    """
    The Trade class is used to represent a trade.
    """

    def __init__(self, symbol, date, direction, entry_price, exit_price, qty):
        self.symbol = symbol
        self.date = date
        self.direction = direction
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.qty = qty
        self.profit = self.calculate_profit()

    @classmethod
    def from_backtrader_trade(cls, trade):
        """
        The from_backtrader_trade function is used to
        convert a backtrader trade
        :param trade:
        :return:
        """
        return cls(
            symbol=trade.data._name,
            date=trade.data.datetime.datetime(),
            direction='buy' if trade.history[0].event == 'buy' else 'sell',
            entry_price=trade.price,
            exit_price=trade.history[-1].price,
            qty=trade.size
        )

    def calculate_profit(self):
        """
        The calculate_profit function is used to calculate the profit of a trade.
        It does this by subtracting the entry price from the exit price.

        Args:
            self: Represent the instance of the class

        Returns:
            The profit of a trade
        """
        return self.exit_price - self.entry_price


class PerformanceStats:
    """
    The PerformanceStats class is used to represent the performance statistics of a strategy.
    """

    def __init__(self, win_rate: float, avg_profit: float, avg_loss: float,
                 max_drawdown: float, sharpe_ratio: float, sortino_ratio: float):
        """
    The __init__ function is called when the class is instantiated.
    It sets up the object with all of its initial values.

    Args:
        self: Represent the instance of the object itself
        win_rate: float: Define the win rate of a strategy
        avg_profit: float: Set the average profit of a strategy
        avg_loss: float: Set the average loss of the strategy
        max_drawdown: float: Calculate the maximum drawdown of a strategy
        sharpe_ratio: float: Define the type of variable that is passed into the function
        sortino_ratio: float: Set the sortino_ratio attribute of the class

    Returns:
        An instance of the class
    """
        self.win_rate = win_rate
        self.avg_profit = avg_profit
        self.avg_loss = avg_loss
        self.max_drawdown = max_drawdown
        self.sharpe_ratio = sharpe_ratio
        self.sortino_ratio = sortino_ratio

    def plot(self):
        # Generate visualization of performance stats
        """
        The plot function generates a visualization of the performance statistics.
                Parameters:
                    None

        Args:
            self: Represent the instance of the class

        Returns:
            A bar graph of the performance statistics

        """
        labels = ['Win rate', 'Avg. profit', 'Avg. loss', 'Max drawdown', 'Sharpe ratio', 'Sortino ratio']
        values = [self.win_rate, self.avg_profit, self.avg_loss, self.max_drawdown, self.sharpe_ratio, self.sortino_ratio]
        plt.bar(labels, values)
        plt.title('Performance Statistics')
        plt.xlabel('Metrics')
        plt.ylabel('Value')
        plt.show()


def calculate_performance_stats(trades: List[Trade]) -> PerformanceStats:
    """
    The calculate_performance_stats function calculates various performance statistics based on a list of trades.

    Args:
        trades: List[Trade]: Pass in a list of trades

    Returns:
        A performances tats object, which is a namedtuple

    """

    if not trades:
        raise ValueError("List of trades is empty.")

    num_trades = len(trades)
    win_trades = [trade for trade in trades if trade.profit > 0]
    num_win_trades = len(win_trades)
    num_loss_trades = num_trades - num_win_trades

    if num_win_trades == 0:
        win_rate = 0.0
        avg_profit = 0.0
    else:
        win_rate = num_win_trades / num_trades
        profits = [trade.profit for trade in win_trades]
        avg_profit = sum(profits) / num_win_trades

    if num_loss_trades == 0:
        avg_loss = 0.0
    else:
        losses = [trade.profit for trade in trades if trade.profit < 0]
        avg_loss = sum(losses) / num_loss_trades

    profits = [trade.profit for trade in trades]
    sharpe_ratio = calculate_sharpe_ratio(profits)
    sortino_ratio = calculate_sortino_ratio(profits)
    max_drawdown = calculate_max_drawdown(profits)

    return PerformanceStats(win_rate, avg_profit, avg_loss, max_drawdown, sharpe_ratio, sortino_ratio)


# Define the parameter space to explore using hyperopt
param_space = dict(
    trading_rules=dict(
        buy_time=hp.uniform('buy_time', 30, 120, 1),
        buy_stop_loss_pct=hp.uniform('buy_stop_loss_pct', 0.001, 0.01),
        buy_take_profit_pct=hp.uniform('buy_take_profit_pct', 0.005, 0.02),
        buy_take_profit_pct2=hp.uniform('buy_take_profit_pct2', 0.01, 0.05),
        buy_green_candle_pct=hp.uniform('buy_green_candle_pct', 0.001, 0.005),
        buy_red_candle_pct=hp.uniform('buy_red_candle_pct', 0.001, 0.005),
        buy_wick_pct=hp.uniform('buy_wick_pct', 0.001, 0.01),
        buy_lot_pct=hp.uniform('buy_lot_pct', 0.001, 0.01),
        buy_ma_period_1=hp.quniform('buy_ma_period_1', 10, 50, 1),
        buy_ma_period_2=hp.quniform('buy_ma_period_2', 50, 200, 1),
        buy_ma_range_min_pct=hp.uniform('buy_ma_range_min_pct', 0.001, 0.01),
        buy_ma_range_max_pct=hp.uniform('buy_ma_range_max_pct', 0.01, 0.05),
        sell_ma_period_1=hp.quniform('sell_ma_period_1', 10, 50, 1),
        sell_ma_period_2=hp.quniform('sell_ma_period_2', 50, 100, 1),
        sell_ma_widening_pct=hp.uniform('sell_ma_widening_pct', 0.003, 0.01),
        sell_take_profit_pct=hp.uniform('sell_take_profit_pct', 0.003, 0.01),
        sell_stop_loss_pct=hp.uniform('sell_stop_loss_pct', 0.003, 0.01),
        stop_trading_red_bars_above_ma_pct=hp.uniform('stop_trading_red_bars_above_ma_pct', 0.005, 0.02),
        ma_cross_sell_enabled=hp.choice('ma_cross_sell_enabled', [True, False])
    )
)


def run_backtest_with_params(params: Dict, stock_data_df=None) -> float:
    # Set up backtesting environment
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=50)

    # Add data feed
    data = bt.feeds.PandasData()
    cerebro.adddata(data)

    # Add strategy
    strategy = BuySellStrategy()
    cerebro.addstrategy(strategy)

    # Run backtest
    result = cerebro.run()
    return result[0].broker.getvalue()


best = fmin(fn=run_backtest_with_params, space=param_space, algo=tpe.suggest, max_evals=100)
print(best)

# Run the backtest with the best parameters found by hyperopt
best_params = {
    'buy_time': 59,
    'buy_stop_loss_pct': best['buy_stop_loss_pct'],
    'buy_take_profit_1_pct': 1,
    'buy_take_profit_2_pct': 2,
    'buy_green_candle_limit_pct': best['buy_green_candle_limit_pct'],
    'buy_red_candle_limit_pct': best['buy_red_candle_limit_pct'],
    'buy_red_candle_stop_loss_pct': 0.2,
    'buy_red_candle_take_profit_pct': 1,
    'buy_wick_size_pct': 0.2,
    'buy_wick_ma_period': 25,
    'buy_qty_pct': 0.2,
    'buy_qty_ma_period': 89,
    'buy_qty_ma_range_min_pct': 0.3,
    'buy_qty_ma_range_max_pct': best['buy_qty_ma_range_max_pct'],
    'sell_ma_period_1': int(best['sell_ma_period_1']),
    'sell_ma_period_2': int(best['sell_ma_period_2']),
    'sell_interval_pct': 0.3,
    'sell_stop_loss_pct': 0.2,
    'sell_take_profit_pct': 1,
    'sell_trailing_stop_pct': 0.3,
    'stop_trading_on_red_bar_above_ma_pct': best['stop_trading_on_red_bar_above_ma_pct'],
    'stop_trading_on_red_bar_above_ma_period': 50,
    'stop_trading_on_red_bar_above_ma_range_min_pct': 0.2,
    'stop_trading_on_red_bar_above_ma_range_max_pct': 0.5,
    'flip_to_sell_on_sell_ma_cross': True,
    'flip_to_sell_on_sell_ma_cross_widening_pct': 0.3
}


class Backtest:
    """
    The Backtest class is used to run a backtest on a strategy and plot the results.
    """
    def __init__(self, data, strategy, params, commission, cash):
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(cash)
        cerebro.broker.setcommission(commission=commission)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=50)
        cerebro.adddata(data)
        cerebro.addstrategy(strategy, **params)
        self.cerebro = cerebro

    def run(self):
        """
        The run function is the main function of the backtrader. It will run through all
        the strategies and indicators that have been added to it, and then plot them on a graph.

        Args:
            self: Represent the instance of the class

        Returns:
            The list of the analyzers that were added to the strategy

        """
        self.cerebro.run()

    def plot(self):
        """
        The plot function is used to plot the results of a backtest.
        It can be called with no arguments, in which case it will use the default settings for plotting.
        Alternatively, you can pass a dictionary of keyword arguments that are passed on to matplotlib.

        Args:
            self: Represent the instance of the class

        Returns:
            A list of matplotlib

        Doc Author:
            Trelent
        """
        self.cerebro.plot()

    def get_value(self):
        """
        The get_value function returns the current value of the portfolio.
        This is a combination of cash and positions.

        Args:
            self: Represent the instance of the class

        Returns:
            The total value of the portfolio
        """
        return self.cerebro.broker.getvalue()

    def get_return(self):
        """
        The get_return function is used to calculate the return of a strategy.
        The function takes in an instance of the Cerebro class and returns a float value representing the return.


        Args:
            self: Allow an object to refer to itself inside of a method

        Returns:
            The value of the broker divided by 100000


        """
        return self.cerebro.broker.getvalue() / 100000.0

    def get_annual_return(self):
        """
        The get_annual_return function returns the annualized return of a given investment.

        Args:
            self: Represent the instance of the class

        Returns:
            The annual return of the investment


        """
        return self.get_return() ** (1 / (self.get_duration_days() / 365.0)) - 1

    def get_sharpe_ratio(self):

        """
        The get_sharpe_ratio function returns the Sharpe ratio of a strategy.

        Args:
            self: Represent the instance of the class

        Returns:
            The sharpe ratio of the strategy

        """
        win_trades = self.cerebro.broker.get_winning_trades()
        win_trades = [trade.history[0].event.pnlcomm for trade in win_trades if trade.isclosed]
        lose_trades = self.cerebro.broker.get_losing_trades()
        lose_trades = [trade.history[0].event.pnlcomm for trade in lose_trades if trade.isclosed]
        return (sum(win_trades) / len(win_trades) - sum(lose_trades) / len(lose_trades)) / np.std(win_trades + lose_trades)

    def get_max_drawdown(self):
        """
        The get_max_drawdown function returns the maximum drawdown of a strategy.

        Args:
            self: Represent the instance of the class

        Returns:
            The maximum drawdown of the strategy


        """
        drawdown = self.cerebro.broker.get_drawdown()
        return max(drawdown, key=lambda x: x[1])[1]

    def get_max_drawdown_period(self):
        """
        The get_max_drawdown_period function returns the maximum drawdown period.

        Args:
            self: Represent the instance of a class

        Returns:
            The maximum drawdown period

        """
        drawdown = self.cerebro.broker.get_drawdown()
        return max(drawdown, key=lambda x: x[2])

    def get_trade_count(self):
        """
        The get_trade_count function returns the number of trades that have been executed by the broker.
        This is useful for determining if a strategy has traded at all, and how many times it has traded.

        Args:
            self: Represent the instance of the class

        Returns:
            The number of trades that have been made in the strategy

        """
        trades = self.cerebro.broker.get_trades()
        return len(trades)

    def get_trade_profit(self):
        """
        The get_trade_profit function returns the sum of all profits from closed trades.

        Args:
            self: Represent the instance of the class

        Returns:
            The total profit of all closed trades


        """
        trades = self.cerebro.broker.get_trades()
        profits = [trade.history[0].event.pnlcomm for trade in trades if trade.isclosed]
        return sum(profits)

    def get_trade_profit_ratio(self):
        """
        The get_trade_profit_ratio function returns the average profit per trade.
        It does this by first getting all of the trades from cerebro, then filtering out only closed trades.
        Then it gets a list of profits for each trade and sums them up to get an overall profit value.
        Finally, it divides that sum by the number of trades to get an average.

        Args:
            self: Access the attributes and methods of the class in python

        Returns:
            The average profit per trade

        """
        trades = self.cerebro.broker.get_trades()
        profits = [trade.history[0].event.pnlcomm for trade in trades if trade.isclosed]
        return sum(profits) / len(profits)

    def get_trade_average_profit(self):
        """
        The get_trade_average_profit function returns the average profit of all closed trades.

        Args:
            self: Represent the instance of the class

        Returns:
            The average profit of all closed trades

        """
        trades = self.cerebro.broker.get_trades()
        profits = [trade.history[0].event.pnlcomm for trade in trades if trade.isclosed]
        return sum(profits) / len(profits)


    def get_trade_won_count(self):
        """
        The get_trade_won_count function returns the number of trades that have been closed and won.

        Args:
            self: Represent the instance of the class

        Returns:
            The number of trades that have been closed and are profitable


        """
        trades = self.cerebro.broker.get_trades()
        won_trades = [trade for trade in trades if trade.isclosed and trade.history[0].event.pnl > 0]
        return len(won_trades)

    def get_trade_lost_count(self):
        """
        The get_trade_lost_count function returns the number of trades that have been closed and resulted in a loss.

        Args:
            self: Represent the instance of the class

        Returns:
            The number of trades that were lost

        """
        trades = self.cerebro.broker.get_trades()
        lost_trades = [trade for trade in trades if trade.isclosed and trade.history[0].event.pnl < 0]
        return len(lost_trades)

    def get_trade_closed_count(self):
        """
        The get_trade_closed_count function returns the number of closed trades.
        :return: int


        Args:
            self: Represent the instance of the class

        Returns:
            The number of closed trades

        """

        trade_closed_count = self.cerebro.broker.get_trade_closed_count()
        trade_count = self.cerebro.broker.get_trade_count()

        return 0 if trade_closed_count == 0 else trade_closed_count / trade_count


bt = Backtest(data, Strategy, params=best_params, commission=0, cash=10000)
bt.run()
bt.plot()
import backtrader as bt


class BuySellStrategy(bt.Strategy):
    params = SimpleNamespace(
        **dict(
        trading_rules=dict(
            buy_time=59,
            buy_stop_loss_pct=0.002,
            buy_take_profit_pct=0.01,
            buy_take_profit_pct2=0.02,
            buy_green_candle_pct=0.003,
            buy_red_candle_pct=0.002,
            buy_wick_pct=0.002,
            buy_lot_pct=0.002,
            buy_ma_period_1=25,
            buy_ma_period_2=89,
            buy_ma_range_min_pct=0.002,
            buy_ma_range_max_pct=0.005,
            sell_ma_period_1=25,
            sell_ma_period_2=89,
            sell_limit_interval_pct=0.003,
            sell_stop_loss_pct=0.002,
            sell_take_profit_pct=0.01,
            sell_stop_protect_time=5,
            max_stop_protect_tries=3,
            max_stop_protect_time=15,
            stop_trading_above_ma_range_pct=0.002,
            flip_to_sell_ma_widen_pct=0.003,
        )
    )
 )

    def __init__(self):
        self.buy_and_hold_returns = None
        self.strategy_vs_buy_and_hold_returns = None
        self.returns = None
        self.order = None
        self.final_portfolio_value = None
        self.sell_order = None
        self.buy_signal_triggered = False
        self.buy_order_placed = False
        self.sell_order_placed = False
        self.buy_limit_price = 0
        self.stop_loss_price = 0
        self.take_profit_price = 0

    def next(self):
        """
        The next function is called on every new candle.
        """
        # Check if buy signal has been triggered
        if self.buy_signal_triggered:
            # Check if a buy order has not been placed
            if not self.buy_order_placed:
                # Place a limit buy order
                self.buy_order_placed = True
                self.buy(
                    exectype=bt.Order.Limit,
                    price=self.buy_limit_price,
                    size=calculate_quantity(self.datas[0], self.params.trading_rules.buy_lot_size_pct)
                )
            elif self.position:
                # Check if the stop loss price has not been set
                if not self.stop_loss_price:
                    # Set stop loss price
                    self.stop_loss_price = self.data.close * (1 - self.params.trading_rules.buy_stop_loss_pct)
                    self.sell(exectype=bt.Order.Stop, price=self.stop_loss_price)

                # Check if the take profit price has not been set
                if not self.take_profit_price:
                    # Set take profit price
                    self.take_profit_price = self.data.close * (1 + self.params.trading_rules.buy_take_profit_pct)
                    self.sell(exectype=bt.Order.Limit, price=self.take_profit_price)

                    # Check if stop loss or take profit has been triggered
                if self.position.size > 0 and (self.data.close <= self.stop_loss_price or self.data.close >= self.take_profit_price):
                    self.close()

                    self._extracted_from_next_36()

        elif self.buy_ma > self.data.close[0] > self.sell_ma:
            # Check if current candle is a red candle
            if (
                self.data.close[0] < self.data.open[0]
                and self.data.close[-1] < self.data.open[-1]
                and self.data.datetime.time().second == 59
            ):
                # Set buy signal triggered flag
                self.buy_signal_triggered = True

                # Calculate buy limit price
                self.buy_limit_price = self.data.close[0] * (1 - self.params.trading_rules.buy_limit_price_pct)

        elif self.data.close[0] > self.buy_ma:
            self._extracted_from_next_36()
        elif self.data.close[0] > self.sell_ma:
            # Check if a sell order is open
            if self.sell_order:
                # If yes, check if it has hit stop loss or take profit
                if self.sell_order.status == Order.Status.FILLED:
                    self.sell_order = None
                elif self.sell_order.stop_price is not None and self.data.close[0] < self.sell_order.stop_price:
                    self.close_sell_order()
                    self.log(f'Sell order {self.sell_order.id} hit stop loss at {self.sell_order.stop_price}')
                elif self.sell_order.limit_price is not None and self.data.close[0] >= self.sell_order.limit_price:
                    self.close_sell_order()
                    self.log(f'Sell order {self.sell_order.id} hit take  self.submit_sell_order()profit at {self.sell_order.limit_price}')
            elif self.should_submit_sell_order:
                self.submit_sell_order()

    # TODO Rename this here and in `next`
    def _extracted_from_next_36(self):
        # Reset variables
        self.buy_signal_triggered = False
        self.buy_order_placed = False
        self.stop_loss_price = 0
        self.take_profit_price = 0

    def submit_sell_order(self):

        """
        Submit a sell order
        """
        self.sell_order = self.sell(exectype=bt.Order.StopLimit,
                                    price=self.data.close[0] * (1 + self.params.trading_rules.sell_limit_interval_pct),
                                    plimit=self.data.close[0] * (1 + self.params.trading_rules.sell_take_profit_pct),
                                    stopprice=self.data.close[0] * (1 - self.params.trading_rules.sell_stop_loss_pct),
                                    valid=self.data.datetime.datetime(0) + datetime.timedelta(minutes=self.params.trading_rules.sell_stop_protect_time),
                                    transmit=False)

        self.log(f'Submitted sell order {self.sell_order.id} at {self.sell_order.created.price}')

    def close_sell_order(self):
        """
        Close the sell order
        """
        self.sell_order.close()
        self.sell_order = None
        self.log(f'Closed sell order {self.sell_order.id}')

    @property
    def should_submit_sell_order(self):
        """
        Check if we should submit a sell order
        """
        return self.sell_order is None and self.sell_ma < self.data.close[0] < self.sell_ma * (1 + self.params.trading_rules.flip_to_sell_ma_widen_pct)

    def notify_order(self, order):
        """
        Notify when an order is submitted, accepted, or rejected
        :param order:
        :return:
        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        """
        Notify when a trade has been completed
        :param trade:
        :return:
        """
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}')

    def stop(self):

        """
        Called when the strategy is closed
        """
        self.log(f'(MA Period {self.params.buy_ma_period_1}) Ending Value {self.broker.getvalue()}')

        # Save the final portfolio value for later inspection
        self.final_portfolio_value = self.broker.getvalue()

        # Calculate the return
        self.returns = self.final_portfolio_value - self.initial_portfolio_value

        # Calculate the buy and hold return
        self.buy_and_hold_returns = self.data.close[0] - self.data.close[self.params.maperiod]

        # Calculate the strategy vs buy and hold return
        self.strategy_vs_buy_and_hold_returns = self.returns - self.buy_and_hold_returns

        # Print the results
        print(f'Parameters: {self.params}')
        print(f'Final Portfolio Value: {self.final_portfolio_value:2f}')
        print(f'Returns: {self.returns:2f}')
        print(f'Buy and Hold Returns: {self.buy_and_hold_returns:2f}')
        print(f'Strategy vs Buy and Hold Returns: {self.strategy_vs_buy_and_hold_returns:2f}')

        # Plot the results
        self.plot_results()

    def plot_results(self):
        """
        Plot the results
        """
        # Get the buy and hold returns
        buy_and_hold_returns = self.data.close[0] - self.data.close[self.params.maperiod]

        # Get the strategy vs buy and hold returns
        strategy_vs_buy_and_hold_returns = self.returns - buy_and_hold_returns

        # Get the figure and the plot
        fig = plt.figure(figsize=(16, 9))
        ax = fig.add_subplot(111)

        # Plot the equity curve
        ax.plot(self.equity_curve, label='Equity Curve')

        # Plot the buy and hold equity curve
        ax.plot(self.buy_and_hold_equity_curve, label='Buy and Hold Equity Curve')

        # Plot the buy and hold equity curve
        ax.plot(self.strategy_vs_buy_and_hold_equity_curve, label='Strategy vs Buy and Hold Equity Curve')

        # Plot the legend
        ax.legend()

        # Plot the title

        ax.set_title(
            f'MA Period: {self.params.maperiod} | Final Portfolio Value: {self.final_portfolio_value:2f} | Returns: {self.returns:2f} | Buy and Hold Returns: {buy_and_hold_returns:2f} | Strategy vs Buy and Hold Returns: {strategy_vs_buy_and_hold_returns:2f}')

        # Show the plot
        plt.show()

    def log(self, txt, dt=None):
        """
        Logging function for the strategy
        """
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} {txt}')

    def get_analysis(self):
        """
        Return the buy and hold returns and strategy vs buy and hold returns
        """
        return dict(
            buy_and_hold_returns=self.buy_and_hold_returns,
            strategy_vs_buy_and_hold_returns=self.strategy_vs_buy_and_hold_returns
        )

    def get_analysis_df(self):
        """
        Return the buy and hold returns and strategy vs buy and hold returns as a dataframe
        """
        return pd.DataFrame(self.get_analysis(), index=[0])

    def get_analysis_df_with_parameters(self):

        """
        Return the buy and hold returns and strategy vs buy and hold returns as a dataframe with the strategy parameters
        """
        return pd.concat([pd.DataFrame(self.params.__dict__, index=[0]), self.get_analysis_df()], axis=1)

    def get_parameters(self):
        """
        Return the strategy parameters
        """
        return self.params.__dict__

    def get_parameters_df(self):
        """
        Return the strategy parameters as a dataframe
        """
        return pd.DataFrame(self.get_parameters(), index=[0])
