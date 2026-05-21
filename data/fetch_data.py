import pandas as pd
import yfinance as yf


def fetch_data(symbol, start, end):
    data = yf.download(symbol, start=start, end=end, progress=False)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.columns = [col.lower() for col in data.columns]
    data = data[["open", "high", "low", "close", "volume"]]
    data.dropna(inplace=True)

    return data
