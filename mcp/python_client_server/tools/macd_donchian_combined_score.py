import numpy as np
import pandas as pd
from server import mcp
from typing import List
import yfinance as yf  



@mcp.tool()
def calculate_macd_score(symbol:str, period:str="1y", fast_period:int=12, slow_period:int=26, signal_period:int=9)-> str:
    """
    Calculate a MACD score between -100 and 100 for the tickek and given period
    first we create the MACD indicator with the parameters fast_period (int): Fast EMA period, slow_period (int): Slow EMA period and signal_period (int): Signal line period
    The MACD score combines three components:

    ### MACD Line Position vs. Signal Line (40%)
    
    - Positive when MACD line is above signal line (bullish)
    - Negative when MACD line is below signal line (bearish)
    
    
    ### MACD Line Position vs. Zero (30%)
    
    - Positive when MACD line is above zero (strong bullish trend)
    - Negative when MACD line is below zero (strong bearish trend)
    
    
    ### Histogram Momentum (30%)
    
    Measures the rate of change in the histogram
    
    - Positive when histogram is increasing (accelerating momentum)
    - Negative when histogram is decreasing (decelerating momentum)
    
    Parameters:
    symbol (str): ticker Yahoo finance 
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Either Use period parameter or use start and end
    fast_period (int) : This parameter defines the period (number of days/periods) for the "fast" Exponential Moving Average (EMA). By default, it's set to 12 periods, which is the standard setting for MACD. This shorter period EMA is more responsive to recent price changes.
    slow_period (int) : This parameter defines the period for the "slow" EMA. By default, it's set to 26 periods, which is also standard. This longer period EMA responds more slowly to price changes and captures longer-term trends.
    signal_period( int) : This parameter defines the period for calculating the signal line, which is an EMA of the MACD line itself. By default, it's set to 9 periods, which is the typical setting. The signal line helps identify potential buy/sell signals when it crosses the MACD line.

    Returns:
    (str) : message with:
    Symbol: {symbol}, Period: {period}
    Latest MACD score: {current_macd_score:.2f}
    Latest component 1. MACD line position relative to signal line (40% of score): {current_line_position:.2f}
    Latest component 3: MACD line position relative to zero (30% of score) {current_zero_position:.2f}
    Latest component 3 Histogram direction and momentum (30% of score) : {current_hist_momentum:.2f}
    """
    

    data = yf.download(symbol, period=period,multi_level_index=False) 
    # Calculate the fast and slow EMAs
    ema_fast = data['Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate the MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate the signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate the MACD histogram
    macd_histogram = macd_line - signal_line
    
    # Create result DataFrame
    macd_data = pd.DataFrame({
        'macd_line': macd_line,
        'signal_line': signal_line,
        'macd_histogram': macd_histogram
    }, index=data.index)
    
    score = pd.Series(0, index=data.index)
    
    # Component 1: MACD line position relative to signal line (40% of score)
    # Normalize using typical range
    typical_range = macd_data['macd_line'].std() * 3  # 3 standard deviations
    
    if typical_range == 0:
        typical_range = 0.001  # Prevent division by zero
        
    line_position = (macd_data['macd_line'] - macd_data['signal_line']) / typical_range
    component1 = line_position.clip(-1, 1) * 40
    
    # Component 2: MACD line position relative to zero (30% of score)
    zero_position = macd_data['macd_line'] / typical_range
    component2 = zero_position.clip(-1, 1) * 30
    
    # Component 3: Histogram direction and momentum (30% of score)
    # Rate of change in histogram (smoothed)
    hist_change = macd_data['macd_histogram'].diff(3).rolling(window=3).mean()
    hist_typical_range = hist_change.std() * 3
    
    if hist_typical_range == 0:
        hist_typical_range = 0.001  # Prevent division by zero
        
    hist_momentum = hist_change / hist_typical_range
    component3 = hist_momentum.clip(-1, 1) * 30
    
    # Combine components
    score = component1 + component2 + component3
    current_macd_score = float(score.iloc[-1])
    current_line_position = float(component1.iloc[-1])
    current_zero_position = float(component2.iloc[-1])
    current_hist_momentum = float(component3.iloc[-1])
    message = f"""
    Symbol: {symbol}, Period: {period}\n
    Latest MACD score: {current_macd_score:.2f}\n
    Latest first component score. MACD line position relative to signal line (40% of score): {current_line_position:.2f}\n
    Latest second component score. MACD line position relative to zero (30% of score): {current_zero_position:.2f}\n
    Latest third component score. Histogram direction and momentum (30% of score) : {current_hist_momentum:.2f}
    """
    return message


@mcp.tool()
def calculate_donchian_channel_score(symbol:str, period:str="1y", window:int=20):
    """
    Calculate Donchian score for the given symbol, period and window period
    Donchian Channel Score (-100 to +100)

    Parameters:
    symbol (str): ticker Yahoo finance 
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Either Use period parameter or use start and end
    window (int): The lookback period for calculating channels upper, middle, and lower bands
    ### Price Position Within Channel (50%)

    - +50 when price is at the upper band
    - 0 when price is at the middle band
    - -50 when price is at the lower band
    
    Donchian Channel Score (-100 to +100). it has 3 components
    
    ### Channel Direction (30%)
    
    - Positive when channel is trending upward
    - Negative when channel is trending downward
    
    
    ### Channel Width Trend (20%)
    
    - Positive when channel is widening (increasing volatility)
    - Negative when channel is narrowing (decreasing volatility)
    Returns:
    (str) : message with:
    Symbol: {symbol}, Period: {period}\n
    Latest donchian band score: {current_donchian_score:.2f}\n
    Latest first component score. Position within the channel (50% of score) 0% at lower band, 50% at middle band, 100% at upper band: {current_line_position:.2f}\n
    Latest second component score. Channel direction (30% of score): {current_zero_position:.2f}\n
    Latest third component score. Channel width trend (20% of score) Narrowing channel is bearish, widening is bullish: {current_hist_momentum:.2f}

    """
    data = yf.download(symbol, period=period,multi_level_index=False) 
    # Calculate upper and lower bands
    upper_band = data['High'].rolling(window=window).max()
    lower_band = data['Low'].rolling(window=window).min()
    
    # Calculate middle band (average of upper and lower)
    middle_band = (upper_band + lower_band) / 2
    
    # Create result DataFrame
    channels = pd.DataFrame({
        'upper': upper_band,
        'middle': middle_band,
        'lower': lower_band
    }, index=data.index)
    

    score = pd.Series(0, index=data.index)
    
    # Component 1: Position within the channel (50% of score)
    # 0% at lower band, 50% at middle band, 100% at upper band
    channel_width = channels['upper'] - channels['lower']
    
    # Prevent division by zero
    channel_width = channel_width.replace(0, 0.001)
    
    position_pct = (data['Close'] - channels['lower']) / channel_width
    component1 = ((position_pct * 2) - 1) * 50  # Scale to -50 to +50
    
    # Component 2: Channel direction (30% of score)
    channel_direction = channels['middle'].diff(5).rolling(window=5).mean()
    channel_direction_range = channel_direction.std() * 3
    
    if channel_direction_range == 0:
        channel_direction_range = 0.001  # Prevent division by zero
        
    normalized_direction = channel_direction / channel_direction_range
    component2 = normalized_direction.clip(-1, 1) * 30
    
    # Component 3: Channel width trend (20% of score)
    # Narrowing channel is bearish, widening is bullish
    width_change = channel_width.diff(5).rolling(window=5).mean()
    width_change_range = width_change.std() * 3
    
    if width_change_range == 0:
        width_change_range = 0.001  # Prevent division by zero
        
    normalized_width = width_change / width_change_range
    component3 = normalized_width.clip(-1, 1) * 20
    
    # Combine components
    score = component1 + component2 + component3
    
    current_donchian_score = float(score.iloc[-1])
    current_line_position = float(component1.iloc[-1])
    current_zero_position = float(component2.iloc[-1])
    current_hist_momentum = float(component3.iloc[-1])
    message = f"""
    Symbol: {symbol}, Period: {period}\n
    Latest donchian band score: {current_donchian_score:.2f}\n
    Latest first component score. Position within the channel (50% of score) 0% at lower band, 50% at middle band, 100% at upper band: {current_line_position:.2f}\n
    Latest second component score. Channel direction (30% of score): {current_zero_position:.2f}\n
    Latest third component score. Channel width trend (20% of score) Narrowing channel is bearish, widening is bullish: {current_hist_momentum:.2f}
    """
    return message


@mcp.tool()
def calculate_combined_score_macd_donchian(macd_score:float, donchian_score:float) -> str:
    """
    Calculate a combined indicator macd donchian score between -100 and 100. and interpretate it
    The combined score is a simple average of the two scores, with equal weight to both indicators.
    ## MACD Score (-100 to +100)

    The MACD score combines three components:

    ### MACD Line Position vs. Signal Line (40%)

    - Positive when MACD line is above signal line (bullish)
    - Negative when MACD line is below signal line (bearish)


    ### MACD Line Position vs. Zero (30%)

    - Positive when MACD line is above zero (strong bullish trend)
    - Negative when MACD line is below zero (strong bearish trend)


    ### Histogram Momentum (30%)

    Measures the rate of change in the histogram

    - Positive when histogram is increasing (accelerating momentum)
    - Negative when histogram is decreasing (decelerating momentum)



    ## Donchian Channel Score (-100 to +100)
    The Donchian score combines three components:

    ### Price Position Within Channel (50%)

    - +50 when price is at the upper band
    - 0 when price is at the middle band
    - -50 when price is at the lower band


    ### Channel Direction (30%)

    - Positive when channel is trending upward
    - Negative when channel is trending downward


    ### Channel Width Trend (20%)

    - Positive when channel is widening (increasing volatility)
    - Negative when channel is narrowing (decreasing volatility)



    ## Combined Score
    The combined score is a simple average of the MACD and Donchian scores, giving equal weight to momentum (MACD) and price range (Donchian) indicators.

    ### How to Interpret the Scores

    ### Individual Score Interpretation
    #### MACD Score:

    - Above +50: Strong bullish momentum
    - +25 to +50: Moderate bullish momentum
    - -25 to +25: Neutral momentum
    - -50 to -25: Moderate bearish momentum
    - Below -50: Strong bearish momentum

    #### Donchian Score:

    - Above +50: Price trending strongly upward, near upper band
    - +25 to +50: Price trending upward, above middle band
    - -25 to +25: Price within middle range of channel
    - -50 to -25: Price trending downward, below middle band
    - Below -50: Price trending strongly downward, near lower band

    #### Combined Score Trading Signals
    The combined score translates directly into trading signals:

    - +75 to +100: Strong Buy
    - +50 to +75: Buy
    - +25 to +50: Weak Buy
    - -25 to +25: Neutral (Hold)
    - -50 to -25: Weak Sell
    - -75 to -50: Sell
    - -100 to -75: Strong Sell
    Parameters:
    macd_score (float): Latest MACD score
    donchian_score (float):  Latest donchian band score
    
    Returns:
    float: Combined score between -100 and 100
    """
    # Equal weight to both indicators
    score= (float(macd_score) + float(donchian_score)) / 2
    # Interpret the combined score
    score = float(score)
    if score > 75:
        return "Strong Buy Signal"
    elif score > 50:
        return "Buy Signal"
    elif score > 25:
        return "Weak Buy Signal"
    elif score > -25:
        return "Neutral"
    elif score > -50:
        return "Weak Sell Signal"
    elif score > -75:
        return "Sell Signal"
    else:
        return "Strong Sell Signal"