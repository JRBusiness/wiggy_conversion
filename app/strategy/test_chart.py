import pandas as pd
import pytest
from datetime import datetime
import pytz

from chart_logic import run_analysis, validate_data, plot_data


@pytest.fixture
def sample_candle_data():
    data = {
        "symbol": ["AAPL", "AAPL", "AAPL", "AAPL"],
        "time": [
            datetime(2022, 1, 1, tzinfo=pytz.utc),
            datetime(2022, 1, 2, tzinfo=pytz.utc),
            datetime(2022, 1, 3, tzinfo=pytz.utc),
            datetime(2022, 1, 4, tzinfo=pytz.utc),
        ],
        "open": [100.0, 101.0, 102.0, 103.0],
        "high": [105.0, 106.0, 107.0, 108.0],
        "low": [95.0, 96.0, 97.0, 98.0],
        "close": [103.0, 104.0, 105.0, 106.0],
        "tick_volume": [1000, 2000, 3000, 4000],
        "spread": [0, 0, 0, 0],
        "real_volume": [10000, 20000, 30000, 40000],
    }
    return pd.DataFrame(data)


def test_validate_data_valid_data(sample_candle_data):
    assert validate_data(sample_candle_data) == True


def test_validate_data_missing_column(sample_candle_data):
    sample_candle_data.drop(columns=["symbol"], inplace=True)
    assert validate_data(sample_candle_data) == False


def test_run_analysis_valid_data(sample_candle_data):
    point_value = 0.1
    candle_data = run_analysis(sample_candle_data, point_value)
    assert candle_data is not None
    assert candle_data.symbol == "AAPL"


def test_run_analysis_empty_data():
    point_value = 0.1
    empty_data = pd.DataFrame()
    candle_data = run_analysis(empty_data, point_value)
    assert candle_data is None


def test_run_analysis_invalid_data(sample_candle_data):
    point_value = 0.1
    sample_candle_data.drop(columns=["open", "close"], inplace=True)
    candle_data = run_analysis(sample_candle_data, point_value)
    assert candle_data is None


def test_plot_data(sample_candle_data):
    with pytest.raises(Exception):
        plot_data(sample_candle_data)  # Assuming plot_data function is not modified for error handling


def test_plot_data_with_indicators(sample_candle_data):
    indicators = ["close", "ema_long", "fib_59"]
    with pytest.raises(Exception):
        plot_data(sample_candle_data, indicators)  # Assuming plot_data function is not modified for error handling
