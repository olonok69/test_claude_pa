from fastapi import FastAPI
import yfinance as yf
from fastapi.responses import HTMLResponse
from typing import List
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import logging
import numpy as np
import pandas as pd
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from utils.yahoo_finance_tools import (
    calculate_bollinger_bands,
    find_swing_points,
    calculate_fibonacci_levels,
    calculate_donchian_channel_score,
    calculate_macd_score,
)
from dotenv import load_dotenv

load_dotenv("./keys/.env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")


# Initialize the MCP server with your tools
mcp = FastMCP(name="Finance Tools")


transport = SseServerTransport("/messages/")


@mcp.tool()
def calculate_macd_score_tool(
    symbol: str,
    period: str = "1y",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> str:
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

    data = yf.download(symbol, period=period, multi_level_index=False)
    # Calculate the fast and slow EMAs
    ema_fast = data["Close"].ewm(span=fast_period, adjust=False).mean()
    ema_slow = data["Close"].ewm(span=slow_period, adjust=False).mean()

    # Calculate the MACD line
    macd_line = ema_fast - ema_slow

    # Calculate the signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Calculate the MACD histogram
    macd_histogram = macd_line - signal_line

    # Create result DataFrame
    macd_data = pd.DataFrame(
        {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "macd_histogram": macd_histogram,
        },
        index=data.index,
    )

    score = pd.Series(0, index=data.index)

    # Component 1: MACD line position relative to signal line (40% of score)
    # Normalize using typical range
    typical_range = macd_data["macd_line"].std() * 3  # 3 standard deviations

    if typical_range == 0:
        typical_range = 0.001  # Prevent division by zero

    line_position = (macd_data["macd_line"] - macd_data["signal_line"]) / typical_range
    component1 = line_position.clip(-1, 1) * 40

    # Component 2: MACD line position relative to zero (30% of score)
    zero_position = macd_data["macd_line"] / typical_range
    component2 = zero_position.clip(-1, 1) * 30

    # Component 3: Histogram direction and momentum (30% of score)
    # Rate of change in histogram (smoothed)
    hist_change = macd_data["macd_histogram"].diff(3).rolling(window=3).mean()
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
def calculate_donchian_channel_score_tool(
    symbol: str, period: str = "1y", window: int = 20
):
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
    data = yf.download(symbol, period=period, multi_level_index=False)
    # Calculate upper and lower bands
    upper_band = data["High"].rolling(window=window).max()
    lower_band = data["Low"].rolling(window=window).min()

    # Calculate middle band (average of upper and lower)
    middle_band = (upper_band + lower_band) / 2

    # Create result DataFrame
    channels = pd.DataFrame(
        {"upper": upper_band, "middle": middle_band, "lower": lower_band},
        index=data.index,
    )

    score = pd.Series(0, index=data.index)

    # Component 1: Position within the channel (50% of score)
    # 0% at lower band, 50% at middle band, 100% at upper band
    channel_width = channels["upper"] - channels["lower"]

    # Prevent division by zero
    channel_width = channel_width.replace(0, 0.001)

    position_pct = (data["Close"] - channels["lower"]) / channel_width
    component1 = ((position_pct * 2) - 1) * 50  # Scale to -50 to +50

    # Component 2: Channel direction (30% of score)
    channel_direction = channels["middle"].diff(5).rolling(window=5).mean()
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
def calculate_combined_score_macd_donchian(
    symbol: str,
    period: str = "1y",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    window: int = 20,
) -> str:
    """
    Calculate a combined indicator macd donchian score between -100 and 100. and interpretate it
    The combined score is a simple average of the two scores, with equal weight to both indicators.
    ## MACD Score (-100 to +100)



    ## Donchian Channel Score (-100 to +100)



    ## Combined Score
    The combined score is a simple average of the MACD and Donchian scores, giving equal weight to momentum (MACD) and price range (Donchian) indicators.


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
    symbol (str): ticker Yahoo finance
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Either Use period parameter or use start and end
    fast_period (int) : This parameter defines the period (number of days/periods) for the "fast" Exponential Moving Average (EMA). By default, it's set to 12 periods, which is the standard setting for MACD. This shorter period EMA is more responsive to recent price changes.
    slow_period (int) : This parameter defines the period for the "slow" EMA. By default, it's set to 26 periods, which is also standard. This longer period EMA responds more slowly to price changes and captures longer-term trends.
    signal_period( int) : This parameter defines the period for calculating the signal line, which is an EMA of the MACD line itself. By default, it's set to 9 periods, which is the typical setting. The signal line helps identify potential buy/sell signals when it crosses the MACD line.
    window (int): The lookback period for calculating channels upper, middle, and lower bands
    Returns:
    float: Combined score between -100 and 100
    """
    # Calculate MACD score
    macd_score = calculate_macd_score(
        symbol=symbol,
        period=period,
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
    )
    # Calculate Donchian score
    donchian_score = calculate_donchian_channel_score(
        symbol=symbol,
        period=period,
        window=window,
    )
    # Equal weight to both indicators
    score = (float(macd_score) + float(donchian_score)) / 2
    # Interpret the combined score
    score = float(score)
    message = f"""
    Symbol: {symbol}, Period: {period}\n
    Latest combined score: {score:.2f}\n
    Latest MACD score: {float(macd_score):.2f}\n
    Latest Donchian score: {float(donchian_score):.2f}\n
    Trading Signal: """
    if score > 75:
        return message + "Strong Buy Signal"
    elif score > 50:
        return message + "Buy Signal"
    elif score > 25:
        return message + "Weak Buy Signal"
    elif score > -25:
        return message + "Neutral"
    elif score > -50:
        return message + "Weak Sell Signal"
    elif score > -75:
        return message + "Sell Signal"
    else:
        return message + "Strong Sell Signal"


@mcp.tool()
def calculate_bollinger_fibonacci_score(
    ticker: str,
    period: str = "1y",
    window: int = 20,
    num_std: int = 2,
    window_swing_points: int = 10,
    fibonacci_levels: List = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
    num_days: int = 3,
) -> str:
    """
    Calculate Bollinger Bands and Fibonacci Retracement strategy score to indicate buy/sell/hold signals.

    The strategy score ranges from -100 to +100 and is categorized into five signal zones:

    +60 to +100: Strong Buy
    +20 to +60: Moderate Buy
    -20 to +20: Hold
    -60 to -20: Moderate Sell
    -100 to -60: Strong Sell

    ### How the Score is Calculated
    The score is a weighted combination of four key components:

    ### Bollinger Band Position (30% weight) - Based on the %B indicator:
    When price is near the lower band (%B close to 0): Positive contribution When price is near the upper band (%B close to 1): Negative contribution

    ### Volatility Assessment (15% weight):
    Considers both current Bollinger Band width and recent changes in width Narrow bands with expanding width can signal potential breakouts High volatility reduces signal
    reliability

    ### Fibonacci Level Interaction (35% weight):
    Highest weight because it's the core of this combined strategy Measures proximity to key Fibonacci levels Considers whether price is bouncing off or breaking through a
    level Accounts for whether the level is acting as support or resistance

    ### Price Momentum (20% weight):
    RSI-like momentum indicator to identify overbought/oversold conditions Oversold conditions (like RSI below 30) contribute positively Overbought conditions
    (like RSI above 70) contribute negatively

    ### How to Use the Strategy Score
    Entry and Exit Signals:
    Enter long positions when the score moves above +60 (Strong Buy) Exit long positions when the score falls below +20 (Hold or lower) Enter short positions when the
    score falls below -60 (Strong Sell) Exit short positions when the score rises above -20 (Hold or higher)

    Position Sizing:
    The magnitude of the score indicates conviction Use higher position sizes when scores are extreme (+90 or -90) Use smaller position sizes when scores are closer to
    thresholds (+65 or -65)

    Confirmation and Risk Management:
    Wait for at least 2-3 consecutive days in the same signal zone before acting Place stop losses based on the nearest Fibonacci level in the opposite direction For long
    positions, consider taking partial profits when approaching key resistance levels For short positions, consider covering partially when approaching key support levels


    Parameters:
    ticker (str): ticker Yahoo finance
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Either Use period parameter or use start and end
    window  (int): period to calculate the middle Bollinger Bands moving average
    num_std (int) : Number of standard deviation to use to calculate lower and upper Bollinger Bands
    window_swing_points (int) : wing points are critical reference points used to identify significant price reversals and establish the Fibonacci retracement levels. This determines how many periods before and after a potential swing point need to be examined
    fibonacci_levels (List[float]): List of float which help us to identify possible resistance and support levels
    num_days (int): Number of days from the last day to calculate scores. Default is 3 (3 last days)

    Returns:
    (str) : message with the scores for the last n days
    """
    data = yf.download(ticker, period=period, multi_level_index=False)
    if data is None or "Upper_Band" not in data.columns:
        calculate_bollinger_bands(
            data=data, window=window, ticker=ticker, num_std=num_std
        )

    if "Swing_High" not in data.columns:
        find_swing_points(data=data, window=window_swing_points)

    # Calculate Fibonacci levels if not already done
    fib_levels, fib_trend = calculate_fibonacci_levels(
        data=data, window=window_swing_points, fibonacci_levels=fibonacci_levels
    )

    # Initialize score column
    data["Strategy_Score"] = 0.0
    data["BB_Score"] = 0.0
    data["Volatility_Score"] = 0.0
    data["Fib_Score"] = 0.0
    data["Momentum_Score"] = 0.0

    # Skip calculation if Fibonacci levels couldn't be determined
    if fib_levels is None:
        return "Unable to calculate Fibonacci levels. Not enough data or no significant swing points found."

    # 1. Score based on %B (position within Bollinger Bands)
    # %B near 0 (price near lower band) = positive score
    # %B near 1 (price near upper band) = negative score
    data["BB_Score"] = (0.5 - data["%B"]) * 50  # Range: -25 to +25

    # 2. Score based on Bollinger Band width (volatility)
    # Lower volatility means more reliable signals
    # Normalize BB width to a range of 0-1 based on recent history
    rolling_max_width = data["BB_Width"].rolling(window=60, min_periods=20).max()
    rolling_min_width = data["BB_Width"].rolling(window=60, min_periods=20).min()

    # Avoid division by zero by adding small epsilon
    width_range = rolling_max_width - rolling_min_width
    width_range = width_range.replace(0, 1e-10)

    normalized_width = (data["BB_Width"] - rolling_min_width) / width_range

    # Expanding BB width (increasing volatility) can signal upcoming trend change
    bb_width_change = data["BB_Width"].pct_change(5)  # 5-day change in BB width

    # Combine into volatility score (range: -15 to +15)
    # Narrow bands with expanding width can signal breakout potential
    data["Volatility_Score"] = 15 - normalized_width * 30 + bb_width_change * 100
    data["Volatility_Score"] = data["Volatility_Score"].clip(-15, 15)

    # 3. Score based on proximity to Fibonacci levels
    data["Closest_Fib_Level"] = None
    data["Closest_Fib_Price"] = np.nan
    data["Fib_Distance_Pct"] = np.nan

    for i in range(len(data)):
        if i < window:  # Skip initial periods without enough data
            continue

        current_price = data["Close"].iloc[i]

        # Find closest Fibonacci level
        closest_fib = min(fib_levels.items(), key=lambda x: abs(x[1] - current_price))
        closest_fib_level, closest_fib_price = closest_fib

        # Store for debugging
        data.loc[data.index[i], "Closest_Fib_Level"] = closest_fib_level
        data.loc[data.index[i], "Closest_Fib_Price"] = closest_fib_price

        # Calculate percent distance to closest Fibonacci level
        percent_distance = abs(current_price - closest_fib_price) / closest_fib_price
        data.loc[data.index[i], "Fib_Distance_Pct"] = percent_distance

        # FIXED: Only consider very close distances to be significant (max 3%)
        if percent_distance > 0.03:
            continue

        # FIXED: Higher score for closer proximity
        proximity_factor = 1.0 - (percent_distance / 0.03)
        proximity_score = 35.0 * proximity_factor  # Max score of 35

        # Get price direction (using 5-day change)
        if i >= 5:
            price_5d_ago = data["Close"].iloc[i - 5]
            price_direction = 1 if current_price > price_5d_ago else -1

            # Determine if we're at support or resistance
            is_support_level = False
            is_resistance_level = False

            # In downtrend, lower Fibonacci levels act as support
            # In uptrend, higher Fibonacci levels act as resistance
            if fib_trend == "downtrend":
                is_support_level = closest_fib_level <= 0.382
                is_resistance_level = closest_fib_level >= 0.618
            else:  # uptrend
                is_support_level = closest_fib_level <= 0.382
                is_resistance_level = closest_fib_level >= 0.618

            # : Simplified scoring logic
            if is_support_level:
                # At support: positive score if price is rising (bouncing), negative if falling (breaking)
                score = proximity_score if price_direction > 0 else -proximity_score
            elif is_resistance_level:
                # At resistance: negative score if price is falling (rejecting), positive if rising (breaking)
                score = -proximity_score if price_direction < 0 else proximity_score
            else:
                # Mid-range fibonacci levels (like 0.5) - use smaller scores
                score = proximity_score * 0.5 * price_direction

            data.loc[data.index[i], "Fib_Score"] = score

    # 4. Score based on momentum
    # RSI-like momentum indicator (simplified)
    price_change = data["Close"].diff(1)
    gain = price_change.clip(lower=0)
    loss = -price_change.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=5).mean()
    avg_loss = loss.rolling(window=14, min_periods=5).mean()

    # Avoid division by zero
    avg_loss_safe = avg_loss.replace(0, 1e-10)
    rs = avg_gain / avg_loss_safe
    rsi = 100 - (100 / (1 + rs))

    # Convert RSI to momentum score (-30 to +30)
    # RSI < 30 = oversold = positive score
    # RSI > 70 = overbought = negative score
    data["Momentum_Score"] = np.where(
        rsi < 30,
        30 * (30 - rsi) / 30,
        np.where(
            rsi > 70,
            -30 * (rsi - 70) / 30,
            (50 - rsi) * 0.6,  # Scaled score for middle range
        ),
    )

    # Combine all scores into the final strategy score
    # Weights: BB 30%, Volatility 15%, Fibonacci 35%, Momentum 20%
    data["Strategy_Score"] = (
        0.30 * data["BB_Score"]
        + 0.15 * data["Volatility_Score"]
        + 0.35 * data["Fib_Score"]
        + 0.20 * data["Momentum_Score"]
    )

    # Handle NaN and infinite values
    data["Strategy_Score"] = (
        data["Strategy_Score"].fillna(0).replace([np.inf, -np.inf], 0)
    )

    # Clip to desired range and round but keep as float
    data["Strategy_Score"] = data["Strategy_Score"].clip(-100, 100).round()

    # Determine signal category - use float values for bins
    data["Signal_Category"] = pd.cut(
        data["Strategy_Score"],
        bins=[-100.0, -60.0, -20.0, 20.0, 60.0, 100.0],
        labels=["Strong Sell", "Moderate Sell", "Hold", "Moderate Buy", "Strong Buy"],
    )

    # Ensure n doesn't exceed available data
    num_days = min(num_days, len(data))

    # Create message with info for last n days
    message = f"""
    Symbol: {ticker}
    Period download data: {period}
    Window Bollinger Bands: {window}
    Fibonacci levels: {str(fibonacci_levels)}
    """

    # Add score information for each day
    for i in range(1, num_days + 1):
        idx = -i  # Index from the end of the dataframe
        day_date = data.index[idx].strftime("%Y-%m-%d")

        bb_score = float(data.iloc[idx].BB_Score)
        volatility_score = float(data.iloc[idx].Volatility_Score)
        fib_score = float(data.iloc[idx].Fib_Score)
        momentum_score = float(data.iloc[idx].Momentum_Score)
        strategy_score = float(data.iloc[idx].Strategy_Score)
        signal_category = str(data.iloc[idx].Signal_Category)

        # Add a day header with clear day identification
        if i == 1:
            day_label = "Latest trading day"
        else:
            day_label = f"{i-1} trading day(s) before latest"

        message += f"""
    =========== {day_label} ({day_date}) ===========
    Bollinger Bands score (30% of score): {bb_score:.2f}
    Volatility score (15% of score): {volatility_score:.2f}
    Fibonacci Retracement score (35% of score): {fib_score:.2f}
    Momentum score (20% of score): {momentum_score:.2f}
    Strategy score: {strategy_score:.2f}
    Signal Category: {signal_category}
        """

    return message


@mcp.tool()
def calculate_bollinger_z_score(symbol: str, period: int = 20) -> str:
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

    closes = data["Close"]
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


async def handle_sse(request):
    # Prepare bidirectional streams over SSE
    async with transport.connect_sse(request.scope, request.receive, request._send) as (
        in_stream,
        out_stream,
    ):
        # Run the MCP server: read JSON-RPC from in_stream, write replies to out_stream
        await mcp._mcp_server.run(
            in_stream, out_stream, mcp._mcp_server.create_initialization_options()
        )


# Build a small Starlette app for the two MCP endpoints
sse_app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        # Note the trailing slash to avoid 307 redirects
        Mount("/messages/", app=transport.handle_post_message),
    ]
)


app = FastAPI()
app.mount("/", sse_app)


@app.get("/health")
def read_root():
    return {"message": "MCP SSE Server is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
