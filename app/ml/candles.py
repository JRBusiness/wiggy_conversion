import yfinance as yf
import talib
import pandas as pd
import plotly.graph_objs as go

# Download last 1 year of SPY data
end = pd.Timestamp.today()
start = end - pd.DateOffset(weeks=2)
data = yf.download('SPY', start=start, end=end, interval='5m')

# Detect candlestick patterns
# Refactored to create a new DataFrame without duplicated indexes
ohlc_data = pd.DataFrame(data=data[['Open', 'High', 'Low', 'Close']].values, index=data.index, columns=['Open', 'High', 'Low', 'Close'])
hammer = talib.CDLHAMMER(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
hanging_man = talib.CDLHANGINGMAN(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
doji = talib.CDLDOJI(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
spinning_top = talib.CDLSPINNINGTOP(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
shooting_star = talib.CDLSHOOTINGSTAR(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
marubozu = talib.CDLMARUBOZU(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
inverted_hammer = talib.CDLINVERTEDHAMMER(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
gravestone = talib.CDLGRAVESTONEDOJI(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
three_soldiers = talib.CDL3WHITESOLDIERS(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
three_crows = talib.CDL3BLACKCROWS(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])


def build_patterns():
    # Create new columns for the patterns
    # Refactored to assign values of candlestick patterns to a new DataFrame

    additional_data = {
        'Doji': doji,
        'Spinning Top': spinning_top,
        'Shooting Star': shooting_star,
        'Marubozu': marubozu
    }
    pattern_data = pd.DataFrame(
        data={
            'Inverted Hammer': inverted_hammer, 'Hammer': hammer, 'Hanging Man': hanging_man,
            'Gravestone Doji': gravestone, 'Three Soldiers': three_soldiers, 'Three Crows': three_crows,
        },
        index=ohlc_data.index
    )
    df = pd.concat([ohlc_data, pattern_data], axis=1)

    # Remove empty pattern data
    # Admonishment for not checking if the DataFrame has duplicated indexes
    if df.duplicated().any():
        print("Warning: Duplicated indexes found in the DataFrame")

    additional_patterns = ['Doji', 'Spinning Top', 'Shooting Star', 'Marubozu']

    patterns = ['Inverted Hammer', 'Hammer', 'Hanging Man', 'Gravestone Doji', 'Three Soldiers', 'Three Crows']
    patterns_data = df[df[patterns].any(axis=1)]
    if patterns_data.empty:
        raise ValueError("No candlestick patterns found in the data")

    candlestick_chart = go.Candlestick(x=df.index,
                                       open=df['Open'],
                                       high=df['High'],
                                       low=df['Low'],
                                       close=df['Close'],
                                       increasing=dict(line=dict(color='#00cc00'), fillcolor='#00cc00'),
                                       decreasing=dict(line=dict(color='#ff0000', width=1), fillcolor='#ff0000'),  # Red
                                       )
    # Create traces for each pattern
    pattern_traces = []
    additional_colors = {'Doji': '#F012BE',
                         'Spinning Top': '#FF851B', 'Shooting Star': '#001f3f',
                         'Marubozu': '#7FDBFF'}
    pattern_marker_colors = {'Inverted Hammer': '#ff00c3', 'Hammer': '#39CCCC', 'Hanging Man': '#FF4136',
                             'Gravestone Doji': '#3D9970', 'Three Soldiers': '#ffa8ed', 'Three Crows': '#ffa8ed'}
    for pattern in patterns:
        pattern_data = patterns_data[pattern][patterns_data[pattern] != 0]
        if not pattern_data.empty:
            # Get the closing prices for the dates when the pattern is identified
            close_prices = df.loc[pattern_data.index, 'Close']

            # Create a trace for each pattern
            pattern_trace = go.Scatter(x=pattern_data.index,
                                       y=close_prices,  # pass the closing prices as y-coordinates
                                       mode='markers',
                                       name=pattern,
                                       marker=dict(symbol='triangle-down-open',
                                                   color=pattern_marker_colors[pattern],
                                                   size=10,
                                                   line=dict(width=1)))
            pattern_traces.append(pattern_trace)

    return candlestick_chart, pattern_traces, patterns


    #



# layout = go.Layout(title='SPY Candlestick Chart with Candlestick Patterns',
#                    xaxis=dict(rangeslider=dict(visible=False)),
#                    hovermode='x')
#
#
# fig = go.Figure(data=[candlestick_chart, *pattern_traces], layout=layout)
#
# fig.update_layout(template='plotly_dark')
#
# fig.show()