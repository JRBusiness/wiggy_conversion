import pandas as pd
import MetaTrader5 as mt5
import plotly.graph_objects as go

mt5.initialize()

trading_hours = [(10, 15)]


class Signals:
    # Define function to calculate EMA
    def calculate_ema(self, data, length):
        return data['close'].ewm(span=length).mean()

    # Define function to calculate ATR
    def calculate_atr(self, data, period):
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(period).mean()

    def calculate_rsi(self, series, window=14):
        close_diff = series.diff(1)
        positive_change = close_diff.where(close_diff > 0, 0)
        negative_change = close_diff.where(close_diff < 0, 0)
        average_gain = positive_change.rolling(window).mean()
        average_loss = negative_change.rolling(window).mean()
        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    # Define function to check trading hours
    def check_trading_hours(self, hour, minute):
        for start, end in trading_hours:
            if start <= hour < end:
                return True
        return False

    # Define function to place order
    def place_order(self, symbol, order_type, volume, price, stop_loss, take_profit):
        if order_type == 'buy':
            trade_type = mt5.ORDER_TYPE_BUY
        elif order_type == 'sell':
            trade_type = mt5.ORDER_TYPE_SELL
        else:
            print('Invalid order type')
            return

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': trade_type,
            'price': price,
            'sl': stop_loss,
            'tp': take_profit,
            'magic': 123456,
            'comment': 'Trade bot order',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        return result

    def check_signal(self, symbol, show_plot=False):
        ema_length = 100
        pip_threshold = 10
        lookback = 100
        atr_period = 14
        gap_window = 100
        bar_limit = 1000
        data = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, lookback))
        # Calculate EMA
        if data.shape[0] < ema_length:
            ema_length = data.shape[0]
        if data.shape[0] < gap_window:
            gap_window = data.shape[0]
        data['ema'] = self.calculate_ema(data, ema_length)
        # Calculate gap
        data['gap'] = data['close'] - data["ema"]
        # Calculate longest gap
        data["longest_gap"] = data["gap"].rolling(window=gap_window).max()
        # Calculate ATR
        data['atr'] = self.calculate_atr(data, atr_period)
        data["buy_condition"] = data["gap"] < 0
        data["sell_condition"] = data["gap"] > 0
        data["wick_size"] = abs(data["high"] - data["low"]) / mt5.symbol_info(symbol).point
        data["buy_wick_condition"] = data["buy_condition"] & (data["wick_size"] >= pip_threshold)
        data["sell_wick_condition"] = data["sell_condition"] & (data["wick_size"] >= pip_threshold)
        data["buy_wick_count"] = data["buy_wick_condition"].rolling(window=bar_limit).sum()
        data["sell_wick_count"] = data["sell_wick_condition"].rolling(window=bar_limit).sum()
        data["fib_59"] = (
                data["low"].shift(1)
                + (data["high"].shift(1) - data["low"].shift(1)) * 0.59
        )
        data["fib_163"] = (
                data["low"].shift(1)
                + (data["high"].shift(1) - data["low"].shift(1)) * 1.63
        )
        data['rsi'] = self.calculate_rsi(data["close"], window=14)
        # Get latest bar
        latest_bar = data.iloc[-1]
        symbol_data = mt5.symbol_info(symbol)
        if show_plot:
            # Ensure the data is sorted by index before plotting
            candle_data = data.sort_index()
            buy_signals = data.loc[data["buy_wick_condition"], :]
            sell_signals = data.loc[data["sell_wick_condition"], :]
            plot_data(candle_data, buy_signals, sell_signals)

        if data["buy_wick_condition"].any():
            entry_price = symbol_data.ask
            return {'symbol': symbol, 'trade_type': 'buy', 'entry_price': entry_price, 'stop_loss': 0,
                    'take_profit': 0}
        elif data["sell_wick_condition"].any():
            entry_price = symbol_data.bid
            return {'symbol': symbol, 'trade_type': 'sell', 'entry_price': entry_price, 'stop_loss': 0,
                    'take_profit': 0}
        return None


def plot_data(candle_data, buy_signals=None, sell_signals=None, indicators=None):
    """
    The plot_data function takes a dataframe of candle data and plots the data and indicators.
    :param candle_data: pd.DataFrame: The dataframe of candle data
    :param buy_signals: pd.DataFrame or None: DataFrame containing buy signals, or None if no buy signals
    :param sell_signals: pd.DataFrame or None: DataFrame containing sell signals, or None if no sell signals
    :param indicators: List[str]: List of indicators or data columns to plot
    :return: None
    """
    if indicators is None:
        indicators = ["close", "ema", "fib_59", "fib_163"]

    fig = go.Figure(data=[go.Candlestick(x=candle_data.index,
                                         open=candle_data['open'],
                                         high=candle_data['high'],
                                         low=candle_data['low'],
                                         close=candle_data['close'],
                                         )])

    # Plot buy signals
    if buy_signals is not None and len(buy_signals) > 0:
        prev_buy_signal_index = None
        for index, row in buy_signals.iterrows():
            if prev_buy_signal_index is None or index - prev_buy_signal_index > 1:
                buy_marker = go.Scatter(x=[index], y=[row['close']],
                                        mode='markers', name='Buy Signal', marker_symbol='triangle-up',
                                        marker=dict(color='green', size=15),
                                        text="Buy Signal", textposition="bottom center")
                fig.add_trace(buy_marker)
                prev_buy_signal_index = index
            elif prev_buy_signal_index is not None and index - prev_buy_signal_index == 1:
                prev_buy_signal_index = index

    # Plot sell signals
    if sell_signals is not None and len(sell_signals) > 0:
        prev_sell_signal_index = None
        for index, row in sell_signals.iterrows():
            if prev_sell_signal_index is None or index - prev_sell_signal_index > 1:
                sell_marker = go.Scatter(x=[index], y=[row['close']],
                                         mode='markers', name='Sell Signal', marker_symbol='triangle-down',
                                         marker=dict(color='red', size=15),
                                         text="Sell Signal", textposition="top center")
                fig.add_trace(sell_marker)
                prev_sell_signal_index = index
            elif prev_sell_signal_index is not None and index - prev_sell_signal_index == 1:
                prev_sell_signal_index = index

    for indicator in indicators:
        fig.add_trace(go.Scatter(x=candle_data.index, y=candle_data[indicator], name=indicator))

    fig.update_layout(title="Candle Data with Buy/Sell Signals", xaxis_title="Date", yaxis_title="Value")
    fig.show()


