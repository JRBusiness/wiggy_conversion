from alpha_vantage.timeseries import TimeSeries
from keras.layers import Dropout
from keras.regularizers import l1_l2
from plotly.subplots import make_subplots
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from loguru import logger
import plotly.graph_objs as go
import talib
import pandas as pd
import numpy as np
from settings import Config

timeframes = ['5min', '15min', '30min', '60min', 'daily']  # the timeframes you want to use


def fetch_data(timeframe):
    ts = TimeSeries(key=Config.alpha_api_key, output_format='pandas')

    if timeframe == 'daily':
        data, meta_data = ts.get_daily(symbol='SPY', outputsize='full')
    else:
        data, meta_data = ts.get_intraday(symbol='SPY', interval=timeframe, outputsize='full')

    data.sort_index(ascending=True, inplace=True)
    data_last_1_year = data.last('1Y')

    cols_to_keep = ['1. open', '2. high', '3. low', '4. close']
    if all(col in data_last_1_year.columns for col in ['5. adjusted close', '6. volume']):
        cols_to_keep.extend(['5. adjusted close', '6. volume'])

    data_last_1_year = data_last_1_year[cols_to_keep]

    return data_last_1_year

def preprocess_data(data):
    ohlc_data = pd.DataFrame(data=data[['1. open', '2. high', '3. low', '4. close']].values,
                             index=data.index,
                             columns=['Open', 'High', 'Low', 'Close'])

    patterns = ['CDLHAMMER', 'CDLHANGINGMAN', 'CDLDOJI', 'CDLSPINNINGTOP', 'CDLSHOOTINGSTAR', 'CDLMARUBOZU',
                'CDLINVERTEDHAMMER']

    for pattern in patterns:
        pattern_function = getattr(talib, pattern)
        result = pattern_function(ohlc_data['Open'], ohlc_data['High'], ohlc_data['Low'], ohlc_data['Close'])
        ohlc_data[pattern] = result

    # Calculate the EMAs
    for period in [9, 26, 100, 740, 1900]:
        ohlc_data[f'EMA_{period}'] = talib.EMA(ohlc_data['Close'], timeperiod=period)

    # # Calculate the Fibonacci retracement levels
    # high = ohlc_data['High'].max()
    # low = ohlc_data['Low'].min()
    # diff = high - low
    # ohlc_data['Fib_0.236'] = high - 0.236 * diff
    # ohlc_data['Fib_0.382'] = high - 0.382 * diff
    # ohlc_data['Fib_0.500'] = high - 0.500 * diff
    # ohlc_data['Fib_0.618'] = high - 0.618 * diff

    ohlc_data.drop(['Open', 'High', 'Low'], axis=1, inplace=True)

    ohlc_data[patterns] = (ohlc_data[patterns] != 0).astype(int)

    close_scaler = MinMaxScaler(feature_range=(0, 1))
    ohlc_data['Close'] = close_scaler.fit_transform(ohlc_data['Close'].values.reshape(-1, 1))

    ohlc_data = ohlc_data.dropna()


    return ohlc_data, close_scaler

def build_model(n_days, n_features):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(n_days, n_features), kernel_regularizer=l1_l2(l1=0.01, l2=0.01), recurrent_regularizer=l1_l2(l1=0.01, l2=0.01), bias_regularizer=l1_l2(l1=0.01, l2=0.01)))
    model.add(Dropout(0.5))
    model.add(LSTM(50, return_sequences=False, kernel_regularizer=l1_l2(l1=0.01, l2=0.01), recurrent_regularizer=l1_l2(l1=0.01, l2=0.01), bias_regularizer=l1_l2(l1=0.01, l2=0.01)))
    model.add(Dropout(0.5))
    model.add(Dense(25, kernel_regularizer=l1_l2(l1=0.01, l2=0.01), bias_regularizer=l1_l2(l1=0.01, l2=0.01)))
    model.add(Dense(1))
    model.compile(optimizer=Adam(0.0001, clipvalue=0.5), loss='mean_squared_error')

    return model

def get_training_data(n_days):

    for timeframe in timeframes:
        data = fetch_data(timeframe)
        ohlc_data = preprocess_data(data)
        dates = ohlc_data[0].index[n_days:]

        scaler = MinMaxScaler(feature_range=(0, 1))
        data_lstm_scaled = scaler.fit_transform(ohlc_data)

        n_features = 13
        x, y = [], []

        for i in range(n_days, len(data_lstm_scaled)):
            x.append(data_lstm_scaled[i - n_days:i])
            y.append(data_lstm_scaled[i, 0])

        x, y = np.array(x), np.array(y)

        train_size = int(len(x) * 0.8)
        x_train_dates = dates[:train_size]
        x_test_dates = dates[train_size:]
        x_train, y_train = x[:train_size], y[:train_size]
        x_test, y_test = x[train_size:], y[train_size:]

        y_train = y_train.ravel()
        y_test = y_test.ravel()
        return y_test, y_train, scaler, x_test, x_train, n_features, train_size, x_train_dates, x_test_dates

def train():
    best_model = None
    best_score = np.inf
    best_timeframe = None

    n_days = 60
    for timeframe in timeframes:
        data = fetch_data(timeframe)
        ohlc_data = preprocess_data(data)

        scaler = MinMaxScaler(feature_range=(0, 1))
        data_lstm_scaled = scaler.fit_transform(ohlc_data)

        n_features = len(ohlc_data.columns)
        x, y = [], []

        for i in range(n_days, len(data_lstm_scaled)):
            x.append(data_lstm_scaled[i - n_days:i])
            y.append(data_lstm_scaled[i, 0])

        x, y = np.array(x), np.array(y)

        train_size = int(len(x) * 0.8)
        x_train, y_train = x[:train_size], y[:train_size]
        x_test, y_test = x[train_size:], y[train_size:]

        y_train = y_train.ravel()
        y_test = y_test.ravel()

        n_features = len(ohlc_data.columns)
        model = build_model(n_days, n_features)
        logger.info(f"Training model on {timeframe} data...")
        model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=8, epochs=50, verbose=1)
        test_score = model.evaluate(x_test, y_test, verbose=0)

        if test_score < best_score:
            best_model = model
            best_score = test_score
            best_timeframe = timeframe
            logger.info(
                f"New best model found for {best_timeframe} with score {best_score}"
            )
            model.save_weights(f'lstm_{timeframe}.h5')
    logger.info(f"Best model was for {best_timeframe} with score {best_score}")

def predict_60(model, data_lstm, n_days, close_scaler) -> Sequential:
    y_test, y_train, scaler, x_test, x_train, n_features, train_size, x_train_dates, x_test_dates, close_scalar = get_training_data(60)

    try:
        model.load_weights('lstm.h5')
    except Exception:
        logger.info("No model found, training a new one")
        model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=8, epochs=50, verbose=1)
        model.save_weights('lstm.h5')

    # Predict next day's price
    last_60_days = x_train[-n_days:]

    if last_60_days.shape[1] != n_days or last_60_days.shape[2] != 13:
        raise ValueError(
            f"Array last_60_days has shape {last_60_days.shape}, but expected (1, {n_days}, {n_features})"
        )



    last_60_days_np = np.reshape(last_60_days[-1], (1, n_days, n_features))
    pred_price = model.predict(last_60_days_np)[0][0]
    pred_price = scaler.inverse_transform(pred_price.reshape(-1, 1))[0][0]
    logger.info(f"Predicted price: {pred_price:.2f}")

    # Evaluate model
    train_score = model.evaluate(x_train, y_train, verbose=0)
    test_score = model.evaluate(x_test, y_test, verbose=0)
    logger.info(f"Train score: {train_score:.2f}")
    logger.info(f"Test score: {test_score:.2f}")

    # Plot the result with plotly in dark mode
    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(
        go.Scatter(x=x_train_dates[n_days:train_size], y=y_train, name='Training Actual', mode='lines',
                   line=dict(color='white')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=x_train_dates[n_days:train_size], y=model.predict(x_train).flatten(),
                   name='Training Predictions', mode='lines', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=x_train_dates[train_size + n_days:], y=y_test, name='Test Actual', mode='lines',
                   line=dict(color='white')),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=x_train_dates[train_size + n_days:], y=model.predict(x_test).flatten(), name='Test Predictions',
                   mode='lines', line=dict(color='blue')),
        row=2, col=1
    )

    fig.update_layout(title='SPY Price Prediction', template='plotly_dark')
    fig.show()
    return model


def scale_data(timeframe):
    data = fetch_data(timeframe)
    ohlc_data, close_scaler = preprocess_data(data)
    n_features = len(ohlc_data.columns)
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_lstm_scaled = scaler.fit_transform(ohlc_data)

    return data_lstm_scaled, scaler, ohlc_data, n_features, close_scaler

if __name__ == "__main__":
    data_lstm, scaler, ohlc_data, n_features, close_scaler = scale_data('5min')

    model = build_model(60, n_features)

    model = predict_60(model, data_lstm, 60, close_scaler)

    logger.info(model.summary())
    #model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=16, epochs=50, verbose=1)

    #model.save_weights('lstm.h5')

    #model.load_weights('lstm.h5')
