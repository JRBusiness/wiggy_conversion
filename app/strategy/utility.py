from typing import List
import pandas as pd


def calculate_ema(data: pd.DataFrame, column: str, ema_length: int) -> pd.Series:
    return data[column].ewm(span=ema_length).mean()


def calculate_bollinger_bands(data: pd.DataFrame, window: int, num_std: int) -> List[pd.Series]:
    rolling_mean = data["close"].rolling(window=window).mean()
    rolling_std = data["close"].rolling(window=window).std()
    upper_band = rolling_mean + num_std * rolling_std
    lower_band = rolling_mean - num_std * rolling_std
    return [upper_band, lower_band]


def calculate_rsi(data: pd.DataFrame, window: int) -> pd.Series:
    delta = data["close"].diff()
    up = delta.where(delta > 0, 0)
    down = -delta.where(delta < 0, 0)
    avg_gain = up.rolling(window=window).mean()
    avg_loss = down.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
