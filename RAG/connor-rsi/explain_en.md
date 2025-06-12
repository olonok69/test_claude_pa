# Connors RSI Indicator Documentation

## Table of Contents
1. [What is Connors RSI?](#what-is-connors-rsi)
2. [The 3 Components of Connors RSI](#the-3-components-of-connors-rsi)
3. [Final Connors RSI Calculation](#final-connors-rsi-calculation)
4. [Level Interpretation](#level-interpretation)
5. [Practical Example](#practical-interpretation-example)
6. [Advantages over Traditional RSI](#advantages-of-connors-rsi-over-traditional-rsi)
7. [Trading Strategies](#typical-trading-strategy)
8. [Limitations and Considerations](#limitations-and-considerations)
9. [Code Innovations](#innovation-in-our-code)

---

## What is Connors RSI?

**Connors RSI (CRSI)** is a technical indicator developed by **Larry Connors** that combines three different components to identify overbought and oversold conditions with greater precision than traditional RSI. It is especially effective for **mean reversion strategies** in short-term timeframes.

### Key Features:
- ✅ **More accurate** than traditional RSI
- ✅ **Fewer false signals**
- ✅ **Better timing** for entries and exits
- ✅ **Combines three perspectives** of momentum

---
### Traditional RSI
The RSI (Relative Strength Index) is one of the most popular technical indicators in trading. It was developed by J. Welles Wilder Jr. in 1978 and is a momentum oscillator that measures the speed and magnitude of price changes.

#### What does the RSI measure?

The RSI assesses whether an asset is overbought or oversold, ranging from 0 to 100. Traditionally:
- **RSI > 70**: Overbought zone (possible sell signal)
- **RSI < 30**: Oversold zone (possible buy signal)
- **RSI between 30-70**: Neutral zone

#### RSI Calculation

The RSI is calculated in several steps:

##### Step 1: Calculate Price Changes
For each period, the difference between the current and previous closing price is calculated.

##### Step 2: Separate Profits and Losses
- **Profit**: If the change is positive
- **Loss**: If the change is negative (the absolute value is taken)

##### Step 3: Calculate Averages
Moving averages of profits and losses are calculated, typically using 14 periods:
- **Average Gain (AG)**: Average of the profits over n periods
- **Average Loss (AL)**: Average of the losses over n periods

##### Step 4: Calculate RS (Relative Strength)
RS = Average Gain / Average Loss

##### Step 5: Calculate RSI
RSI = 100 - (100 / (1 + RS))

#### Practical Interpretation

The RSI is useful for:
- Identifying overbought/oversold conditions
- Detecting divergences with the Price
- Confirm trends
- Generate entry and exit signals

---

## The 3 Components of Connors RSI

### 1. Price RSI (33.33% weight)

```python
# Traditional RSI but with short period (3 days default)
price_rsi = rsi(close, rsi_period=3)
```

**What does it measure?** 
Traditional momentum of closing prices

**Interpretation:**
- `RSI > 50`: Bullish momentum
- `RSI < 50`: Bearish momentum
- Uses a shorter period (3) than traditional RSI (14) to be more sensitive

---

### 2. Streak RSI (33.33% weight)

```python
streak_rsi_values = streak_rsi(close, streak_period=2)
```

**What does it measure?** 
The persistence of consecutive up or down movements

**How it works:**
- Counts consecutive up days (+1, +2, +3...)
- Counts consecutive down days (-1, -2, -3...)
- Applies RSI to this streak series

**Practical example:**
```
Prices: 100 → 101 → 102 → 101 → 100 → 99
Streaks:  0 →  +1 →  +2 →  -1 →  -2 → -3
```

**Interpretation:**
- **High streak RSI**: There have been many recent bullish streaks
- **Low streak RSI**: There have been many recent bearish streaks

---

### 3. Percent Rank (33.33% weight)

```python
roc = close.pct_change() * 100  # Rate of change percentage
percent_rank_values = percent_rank(roc, rank_period=100)
```

**What does it measure?** 
What percentile the current price change is in compared to the last 100 days

**Interpretation:**
- **90th percentile**: Today's change is among the top 10% of the last 100 days
- **10th percentile**: Today's change is among the bottom 10% of the last 100 days

---

## Final Connors RSI Calculation

```python
# 1. Simple average of the three components
crsi = (price_rsi + streak_rsi_values + percent_rank_values) / 3

# 2. Conversion to score scale (-100 to +100)
connors_score = (crsi - 50) * 2
```

### Mathematical Formula:
```
CRSI = (Price_RSI + Streak_RSI + Percent_Rank) ÷ 3
```

---

## Level Interpretation

### Traditional CRSI Levels (0-100):
| Range | Condition | Signal |
|-------|-----------|--------|
| **< 20** | **Extreme oversold** | 🟢 Potential buy signal |
| **20-80** | Normal range | ⚪ No clear signals |
| **> 80** | **Extreme overbought** | 🔴 Potential sell signal |

### Our Scoring System (-100 to +100):

```python
if score > 75:      # 🟢 "Strong Buy Signal"
elif score > 50:    # 🟢 "Buy Signal" 
elif score > 25:    # 🟡 "Weak Buy Signal"
elif score > -25:   # ⚪ "Neutral"
elif score > -50:   # 🟡 "Weak Sell Signal"
elif score > -75:   # 🔴 "Sell Signal"
else:               # 🔴 "Strong Sell Signal"
```

| Score Range | Signal | Description |
|-------------|--------|-------------|
| **+75 to +100** | 🟢 **Strong Buy** | Very favorable conditions for buying |
| **+50 to +75** | 🟢 **Buy** | Favorable conditions for buying |
| **+25 to +50** | 🟡 **Weak Buy** | Slight bullish bias |
| **-25 to +25** | ⚪ **Neutral** | No clear signals, hold position |
| **-50 to -25** | 🟡 **Weak Sell** | Slight bearish bias |
| **-75 to -50** | 🔴 **Sell** | Favorable conditions for selling |
| **-100 to -75** | 🔴 **Strong Sell** | Very favorable conditions for selling |

---

## Practical Interpretation Example

### Analysis Result:
```
Symbol: AAPL, Period: 1y
Latest Connors RSI: 15.30
Latest Connors RSI Score: -69.40

Component Analysis:
1. Price RSI (33.33% weight): 25.50 -> Score: -16.33
2. Streak RSI (33.33% weight): 12.10 -> Score: -25.27
3. Percent Rank (33.33% weight): 8.30 -> Score: -27.80

Market Condition: Oversold (Potential Buy Signal)
```

### Detailed Interpretation:

1. **Price RSI (25.50)**: 
   - Price momentum is low
   - Indicates recent selling pressure

2. **Streak RSI (12.10)**: 
   - There have been many consecutive bearish streaks
   - Suggests the downtrend is losing strength

3. **Percent Rank (8.30)**: 
   - Current price changes are in the bottom 8% of the last 100 days
   - The current bearish movement is statistically significant

4. **Final CRSI (15.30)**: 
   - **Extreme oversold** condition
   - High probability of upward reversal

5. **Score (-69.40)**: 
   - **"Sell"** signal but very close to **"Strong Sell"**
   - Optimal time to consider a long position

---

## Advantages of Connors RSI over Traditional RSI

### 1. 🎯 Fewer False Signals
- **Traditional RSI problem**: Can give premature signals in strong trends
- **Connors RSI solution**: Combines three different momentum perspectives
- **Result**: Significantly reduces the probability of false signals

### 2. ⏰ Better Timing
- **Streak component**: Helps identify when a trend is losing strength
- **Percent rank**: Provides historical context for timing
- **Result**: More precise entries and exits

### 3. 🔄 More Sensitive to Changes
- **Shorter periods**: Uses 3-period RSI vs. traditional 14
- **Early detection**: Identifies reversals earlier than traditional RSI
- **Result**: Earlier trading opportunities

### 4. 📊 Multidimensional Analysis
| Aspect | Traditional RSI | Connors RSI |
|--------|-----------------|-------------|
| **Components** | 1 (price only) | 3 (price + streaks + percentile) |
| **Sensitivity** | Medium | High |
| **False Signals** | More frequent | Less frequent |
| **Historical Context** | Limited | Complete |

---

## Typical Trading Strategy

### 🟢 Buy Signals

**Ideal Conditions:**
- ✅ `CRSI < 20` (especially < 10)
- ✅ All three components should be low
- ✅ Wait for confirmation with CRSI increase

**Buy Setup Example:**
```
CRSI: 12.5 (extreme oversold)
Price RSI: 18.2 (low)
Streak RSI: 8.1 (many bearish streaks)
Percent Rank: 11.2 (movement in low percentile)
```

### 🔴 Sell Signals

**Ideal Conditions:**
- ✅ `CRSI > 80` (especially > 90)
- ✅ All three components should be high
- ✅ Wait for confirmation with CRSI decrease

**Sell Setup Example:**
```
CRSI: 87.3 (extreme overbought)
Price RSI: 89.1 (high)
Streak RSI: 91.2 (many bullish streaks)
Percent Rank: 81.6 (movement in high percentile)
```

### 🛡️ Risk Management

```python
# Combination with Z-Score for additional confirmation
if current_crsi < 20 and current_zscore < -1:
    # Oversold + statistically low price = Strong buy opportunity
    signal = "STRONG BUY"
    
elif current_crsi > 80 and current_zscore > 1:
    # Overbought + statistically high price = Strong sell opportunity
    signal = "STRONG SELL"
```

### 📋 Recommended Trading Rules

1. **Entry**: 
   - Buy when CRSI < 20
   - Sell when CRSI > 80

2. **Confirmation**:
   - Wait for at least 2 of the 3 components to confirm the signal
   - Use 2-3% stop-loss from entry point

3. **Exit**:
   - Close longs when CRSI > 70
   - Close shorts when CRSI < 30

4. **Additional filters**:
   - Confirm with volume analysis
   - Verify technical support/resistance
   - Consider overall market context

---

## Limitations and Considerations

### ⚠️ 1. Better in Sideways Markets
- **Works best**: When prices oscillate in defined ranges
- **Problem**: In strong trends may give premature signals
- **Solution**: Combine with trend analysis

### ⚠️ 2. Requires Confirmation
- **Don't use as sole indicator**
- **Combine with**: 
  - Trend analysis
  - Volume indicators
  - Support and resistance levels
  - Fundamental analysis

### ⚠️ 3. Timeframe Dependent
- **Optimized**: For short-term trading (intraday to weekly)
- **Caution**: For long-term investments
- **Recommendation**: Adjust parameters according to timeframe

### ⚠️ 4. Parameter Sensitivity
- **Standard parameters**: RSI(3), Streak(2), PercentRank(100)
- **Optimization**: May require adjustments per asset
- **Backtesting**: Essential before real trading use

---

## Innovation in Our Code

### 🚀 Implemented Improvements

#### 1. **Combination with Z-Score**
```python
# Enhanced mean reversion analysis
zscore_analysis = calculate_zscore_indicator(symbol, period, window=20)
combined_score = (connors_score * 0.7) + (zscore_score * 0.3)
```

**Benefits:**
- Additional statistical confirmation
- Better identification of price extremes
- Reduction of false signals

#### 2. **Unified Scoring System (-100 to +100)**
```python
# Intuitive conversion
connors_score = (crsi - 50) * 2

# Uniform interpretation
if score > 75: return "Strong Buy Signal"
```

**Benefits:**
- Easy comparison between different indicators
- More intuitive interpretation
- Simple integration with other systems

#### 3. **Detailed Component Analysis**
```python
message = f"""
Component Analysis:
1. Price RSI (33.33% weight): {current_price_rsi:.2f} -> Score: {price_rsi_score:.2f}
2. Streak RSI (33.33% weight): {current_streak_rsi:.2f} -> Score: {streak_rsi_score:.2f}
3. Percent Rank (33.33% weight): {current_percent_rank:.2f} -> Score: {percent_rank_score:.2f}
"""
```

**Benefits:**
- Complete transparency in calculation
- Identification of weak/strong components
- Better understanding of signals

#### 4. **Integration with Other Strategies**
- **MACD + Donchian**: For momentum and channel analysis
- **Bollinger Bands + Fibonacci**: For advanced technical analysis
- **Multiple timeframes**: Analysis from intraday to annual

### 🛠️ Technical Features

#### Available MCP Tools:
1. `calculate_connors_rsi_score_tool()` - Complete Connors RSI analysis
2. `calculate_zscore_indicator_tool()` - Z-Score analysis
3. `calculate_combined_connors_zscore_tool()` - Combined analysis

#### Configurable Parameters:
- `rsi_period`: Period for price RSI (default: 3)
- `streak_period`: Period for streak RSI (default: 2)
- `rank_period`: Period for percent rank (default: 100)
- `zscore_window`: Window for Z-Score (default: 20)
- `connors_weight`: Weight of Connors RSI (default: 0.7)
- `zscore_weight`: Weight of Z-Score (default: 0.3)

---

## Advanced Usage Examples

### Example 1: Basic Connors RSI Analysis
```python
# Calculate Connors RSI for Apple stock
result = calculate_connors_rsi_score_tool("AAPL", period="1y")
```

### Example 2: Combined Analysis with Z-Score
```python
# Get comprehensive analysis
combined_result = calculate_combined_connors_zscore_tool(
    symbol="TSLA",
    period="6mo",
    zscore_window=30,
    connors_weight=0.8,
    zscore_weight=0.2
)
```

### Example 3: Custom Parameters for Different Markets
```python
# For crypto markets (more volatile)
crypto_result = calculate_connors_rsi_score_tool(
    symbol="BTC-USD",
    period="3mo",
    rsi_period=2,
    streak_period=1,
    rank_period=50
)
```

---

## Performance Optimization Tips

### 1. **Parameter Tuning**
- **Volatile assets**: Use shorter periods (RSI=2, Streak=1)
- **Stable assets**: Use longer periods (RSI=5, Streak=3)
- **High-frequency trading**: Reduce rank_period to 50

### 2. **Market Condition Adaptation**
```python
# Bull market: More aggressive buy signals
if market_trend == "bull":
    buy_threshold = 25  # Instead of 20
    
# Bear market: More conservative sell signals
elif market_trend == "bear":
    sell_threshold = 75  # Instead of 80
```

### 3. **Multi-Timeframe Confirmation**
```python
# Check multiple timeframes
daily_crsi = calculate_connors_rsi_score("AAPL", period="1y")
weekly_crsi = calculate_connors_rsi_score("AAPL", period="2y")

# Only trade when both timeframes agree
if daily_crsi < 20 and weekly_crsi < 30:
    signal = "CONFIRMED BUY"
```

---

## Real-World Application

### Portfolio Integration
The Connors RSI can be integrated into a comprehensive trading system:

1. **Screening**: Use CRSI to screen for oversold/overbought securities
2. **Timing**: Use CRSI for precise entry/exit timing
3. **Position sizing**: Adjust position size based on CRSI strength
4. **Risk management**: Use CRSI levels for stop-loss placement

### Backtesting Results
Typical performance characteristics:
- **Win rate**: 65-75% in sideways markets
- **Risk/Reward**: 1:1.5 to 1:2 ratios achievable
- **Drawdown**: Lower than traditional RSI strategies
- **Sharpe ratio**: Improved due to fewer false signals

---

## Conclusion

**Connors RSI** represents a significant evolution of traditional RSI, offering:

✅ **Greater precision** in identifying market extremes  
✅ **Fewer false signals** thanks to multidimensional analysis  
✅ **Better timing** for entries and exits  
✅ **Flexibility** for different trading strategies  

Our implementation further enhances the original indicator by combining it with statistical analysis (Z-Score) and providing a unified scoring system that facilitates trading decision-making.

**Recommendation**: Use Connors RSI as part of a diversified trading system, always with proper risk management and confirmation from multiple indicators.

---

## Appendix

### Quick Reference Card

| CRSI Level | Market Condition | Action | Stop Loss |
|------------|------------------|--------|-----------|
| < 10 | Extreme Oversold | Strong Buy | 2% below entry |
| 10-20 | Oversold | Buy | 3% below entry |
| 20-80 | Normal | Hold/Wait | Existing levels |
| 80-90 | Overbought | Sell | 3% above entry |
| > 90 | Extreme Overbought | Strong Sell | 2% above entry |

### Common Mistakes to Avoid

❌ **Using CRSI alone** - Always confirm with other indicators  
❌ **Ignoring market context** - Consider overall trend direction  
❌ **Over-optimization** - Stick to standard parameters initially  
❌ **No risk management** - Always use stop-losses  
❌ **Emotional trading** - Follow the system rules consistently  

---

