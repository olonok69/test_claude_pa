import numpy as np
import pandas as pd
from server import mcp
from typing import List
import yfinance as yf  



@mcp.tool()
def calculate_bollinger_z_score(symbol:str, period: int = 20)-> str:
    """This tool is used to calculate the Bollinger Z Score
    I get A symbol name in the variable symbol and a period and I calculate a the Score
    the Bollinger Z-Score is a technical indicator used to assess the position of a security's price relative to its Bollinger Bands. It's a normalized measure that helps traders understand whether a price is relatively high or low compared to its recent trading range.

    Here's how to interpret the Bollinger Z-Score:
    
    Z-Score of 0: The current price is exactly at the middle Bollinger Band (the simple moving average).
    Positive Z-Score: The price is above the middle Bollinger Band. The higher the Z-Score, the further the price is above the average and the more "overbought" the security may be considered.
    Negative Z-Score: The price is below the middle Bollinger Band. The lower the Z-Score, the further the price is below the average and the more "oversold" the security may be considered.
    General guidelines for interpretation:
    
    Z-Score > +2: The price is considered overbought. It might be a good time to consider selling or shorting the security.
    Z-Score < -2: The price is considered oversold. It might be a good time to consider buying the security.
    Z-Score between -2 and +2: The price is within the "normal" trading range.
    Important considerations:
    
    Trend: The Z-Score should be interpreted in conjunction with the overall trend. In an uptrend, overbought conditions may persist, while in a downtrend, oversold conditions may persist.
    Volatility: The Z-Score is affected by volatility. A more volatile security will have a wider Bollinger Band and potentially larger Z-Score fluctuations.
    False Signals: The Z-Score can generate false signals, especially in trending markets. It's important to use other technical indicators and fundamental analysis to confirm trading decisions.

    Args:
        symbol (str): symbol to calculate the z-score.
        period  (int): period to calculate the score
        Returns:
        str:  Message with the relevant valuest

    """
    # Fetch historical data
    data = yf.download(symbol, period=f"{period+50}d")
    if data.empty:
        return f"Could not find data for symbol: {symbol}"

    closes = data['Close']
    rolling_mean = closes.rolling(window=period).mean()
    rolling_std = closes.rolling(window=period).std()
    upper_band = rolling_mean + (2 * rolling_std)
    lower_band = rolling_mean - (2 * rolling_std)
    z_score = (closes - rolling_mean) / rolling_std

    latest_z_score = z_score.iloc[-1].values[0]
    latest_upper_band = upper_band.iloc[-1].values[0]
    latest_lower_band = lower_band.iloc[-1].values[0]
    latest_close = closes.iloc[-1].values[0]
    
    message = f"""
    Symbol: {symbol}, Period: {period}\n
    Latest Close: {latest_close:.2f}\n
    Latest Upper Band: {latest_upper_band:.2f}\n
    Latest Lower Band: {latest_lower_band:.2f}\n
    Latest Bollinger Z-score: {latest_z_score:.2f}
    """
    return message