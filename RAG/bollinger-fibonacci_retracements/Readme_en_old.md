# Bollinger Bands and Fibonacci Retracement Strategy

## Bollinger Bands
Bollinger Bands are a technical indicator consisting of three lines: a moving average (typically 20 periods) and two external bands placed at specific standard deviation distances (usually 2) above and below the moving average. These bands show price volatility and help identify when an asset is overbought or oversold.

## Fibonacci Retracement
Support levels are areas where price historically stops falling and bounces upward, functioning as a "floor." Resistance levels are areas where price tends to stop and retreat, acting as a "ceiling" that makes it difficult for price to continue rising.

Fibonacci Retracement levels are horizontal levels that indicate possible areas of support and resistance based on Fibonacci numbers. These levels (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%) are calculated between significant high and low points, and typically act as zones where price may bounce or retrace.

## How the Combined Strategy Works
This strategy combines Bollinger Bands with Fibonacci Retracements to identify more precise buy and sell signals. It works as follows:

Buy signals are generated when price crosses above the lower Bollinger Band and is close to (within 2%) a Fibonacci support level.
  - In an uptrend, these levels act as support (when price retraces)
  - In a downtrend, they function as resistance (when price bounces)
Sell signals are generated when price crosses below the upper Bollinger Band and is close to a Fibonacci resistance level.

This combination helps filter out false signals that might be generated if only one indicator were used.

On the charts, buy signals appear as green triangles pointing upward when price bounces off the lower band and coincides with a Fibonacci level. Sell signals appear as red triangles pointing downward when price retreats from the upper band and coincides with a Fibonacci level. This strategy is especially useful in range-bound markets, where Bollinger Bands can identify price extremes and Fibonacci levels confirm potential reversal zones.

# Interpreting the Bollinger Bandwidth & %B Chart

The "Bollinger Bandwidth & %B" chart that appears at the bottom of the visualization provides valuable complementary information for the strategy:

## Bollinger Bandwidth
- **What it is**: The difference between the upper and lower bands divided by the moving average. It measures market volatility.
- **Interpretation**:
  - A high value indicates high volatility (widely separated bands)
  - A low value indicates low volatility (tightly compressed bands)
  - When it reaches minimums, it often precedes strong movements (volatility expansion)
  - Used to identify market "compressions" that typically precede significant directional movements

## %B Indicator
- **What it is**: Indicates where price is in relation to the Bollinger Bands.
- **Key values**:
  - 0 = price at the lower band
  - 0.5 = price at the moving average
  - 1 = price at the upper band
  - >1 = price above the upper band (overbought)
  - <0 = price below the lower band (oversold)
- **Interpretation**:
  - Serves as an overbought/oversold indicator
  - Crosses above 0 can confirm buy signals
  - Crosses below 1 can confirm sell signals
  - Divergences between %B and price can anticipate reversals
  - In an uptrend, these levels act as support (when price retraces)
  - In a downtrend, they function as resistance (when price bounces)

These indicators complement the main strategy by helping to:
1. Identify periods of low volatility (compression) that often precede important movements
2. Confirm buy and sell signals
3. Determine the strength of trends and potential reversals

When you combine the reading of these indicators with the main strategy signals (band crossovers near Fibonacci levels), you get a more complete set of information for making more informed trading decisions.

# Bollinger Bands and Fibonacci Retracement Strategy

This strategy combines two powerful technical tools to identify trading opportunities:

## Bollinger Bands

Bollinger Bands are an indicator that measures an asset's volatility and consists of:

- **Middle Line**: A moving average (typically 20 periods)
- **Upper Band**: The moving average + 2 standard deviations
- **Lower Band**: The moving average - 2 standard deviations

### Interpretation:
- Prices tend to move between the upper and lower bands
- When price touches or exceeds the upper band, it may indicate overbought conditions
- When it touches or falls below the lower band, it may indicate oversold conditions
- The narrowing of bands (low volatility) often precedes strong movements

## Fibonacci Retracements

Fibonacci retracements use number sequences to identify potential support and resistance levels. The most common levels are:

- 0% (the lowest point of the movement)
- 23.6%
- 38.2%
- 50%
- 61.8%
- 78.6%
- 100% (the highest point of the movement)

### Interpretation:
- In an uptrend, these levels act as support (when price retraces)
- In a downtrend, they function as resistance (when price bounces)

## How the Combined Strategy Works

This strategy identifies trading opportunities by combining both techniques:

1. **Trend Identification**:
   - Significant swing points (highs and lows) are identified
   - Fibonacci levels are drawn between these points

2. **Buy Signals**:
   - Price touches the lower Bollinger Band (possible oversold)
   - Price coincides with or is near an important Fibonacci level
   - This increases the probability of a bounce

3. **Sell Signals**:
   - Price touches the upper Bollinger Band (possible overbought)
   - Price coincides with or is near an important Fibonacci level
   - This increases the probability of a drop

4. **Scoring System**:
   - The strategy includes a scoring system ranging from -100 to +100
   - Above +60: Strong buy signal
   - Between +20 and +60: Moderate buy signal
   - Between -20 and +20: Hold position
   - Between -60 and -20: Moderate sell signal
   - Below -60: Strong sell signal

## Score Components

The score is based on four factors:

1. **Position relative to Bollinger Bands (30% weight)**:
   - If price is near the lower band: positive contribution
   - If it's near the upper band: negative contribution

2. **Volatility Assessment (15% weight)**:
   - Analyzes band width and recent changes
   - Narrow bands beginning to expand may signal potential breakouts

3. **Fibonacci Level Interaction (35% weight)**:
   - Highest weight because it's the core of this combined strategy
   - Measures proximity to key Fibonacci levels
   - Considers whether price is bouncing off or breaking through a level
   - Takes into account whether the level acts as support or resistance

4. **Price Momentum (20% weight)**:
   - Uses an RSI-like indicator to identify overbought/oversold conditions
   - Oversold conditions (RSI below 30) contribute positively
   - Overbought conditions (RSI above 70) contribute negatively


### Confirmation and risk management:
- Wait for 2-3 consecutive days in the same signal zone before acting
- Place stop loss at the nearest Fibonacci level in the opposite direction
- Consider taking partial profits when approaching key resistance/support levels

## Chart Interpretation

In the first chart we see:
- AAPL price with Bollinger Bands (blue bands)
- Fibonacci levels (colored horizontal lines)
- Buy signals (green triangles) and sell signals (red triangles)
- %B and Bandwidth indicators at the bottom

In the second chart we see:
- AAPL price with Bollinger Bands at the top
- Strategy score indicator at the bottom
- Colored zones representing different trading signals:
  - Dark green: Strong buy
  - Light green: Moderate buy
  - Gray: Hold
  - Orange: Moderate sell
  - Red: Strong sell

## Bollinger Bands, Fibonacci Levels, Buy/Sell Signals, Bollinger Bandwidth and %B
![Strategy](strategi_fibonnaci.png)

## Strategy and Scoring System Signals
![Strategy](strategy_score.png)