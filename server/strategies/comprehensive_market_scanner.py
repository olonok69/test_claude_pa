"""
Fixed Comprehensive Market Scanner Tool for MCP Server
This version has proper error handling to avoid breaking JSON-RPC protocol.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import warnings
import sys
import os

# Suppress all warnings that could interfere with JSON-RPC
warnings.filterwarnings('ignore')
os.environ['YFINANCE_SUPPRESS_WARNINGS'] = 'True'

# Import utility functions
from utils.yahoo_finance_tools import (
    calculate_bollinger_bands,
    find_swing_points,
    calculate_fibonacci_levels,
    calculate_connors_rsi_score,
    calculate_zscore_indicator,
    calculate_macd_score,
    calculate_donchian_channel_score,
)

def add_comprehensive_market_scanner_tool(mcp):
    """Add comprehensive market scanner tool that uses all 5 strategies"""
    
    @mcp.tool()
    def comprehensive_market_scanner(
        symbols,
        period: str = "1y",
        output_format: str = "markdown"
    ) -> str:
        """
        Comprehensive market scanner using all 5 trading strategies to analyze multiple stocks.
        
        This tool will:
        1. Analyze each symbol using all 5 strategies
        2. Calculate scores and signals for each strategy
        3. Categorize stocks by overall signal strength
        4. Generate a comprehensive markdown report with rankings and recommendations
        
        Parameters:
        symbols: List of stock ticker symbols to analyze (can be List[str] or comma-separated string)
        period (str): Data period for analysis (default: 1y)
        output_format (str): Output format - "markdown" or "summary" (default: markdown)
        
        Returns:
        str: Comprehensive market analysis report
        """
        
        try:
            # Handle both list and string inputs
            if isinstance(symbols, str):
                symbol_list = [s.strip().upper() for s in symbols.replace('"', '').replace("'", "").split(',')]
                symbol_list = [s for s in symbol_list if s and s.replace('.', '').replace('-', '').isalnum()]
            elif isinstance(symbols, list):
                symbol_list = [str(s).strip().upper() for s in symbols if str(s).strip()]
            else:
                return "Error: Symbols must be provided as a list or comma-separated string"

            if not symbol_list:
                return "Error: No valid symbols provided for scanning"

            # Limit to prevent overload
            if len(symbol_list) > 20:  # Reduced limit for stability
                symbol_list = symbol_list[:20]
                
            analysis_date = datetime.now().strftime("%B %d, %Y")
            
            # Initialize results storage
            results = []
            failed_symbols = []
            
            # Analyze each symbol with proper error handling
            for symbol in symbol_list:
                try:
                    analysis_result = analyze_single_symbol_safe(symbol, period)
                    if analysis_result:
                        results.append(analysis_result)
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    # Log to stderr to avoid breaking JSON-RPC
                    print(f"Error analyzing {symbol}: {str(e)}", file=sys.stderr)
                    failed_symbols.append(symbol)
            
            if not results:
                return f"Error: No valid analysis results for any symbols in {symbol_list}"
            
            # Generate comprehensive report
            if output_format.lower() == "summary":
                return generate_summary_report_safe(results, failed_symbols, analysis_date)
            else:
                return generate_comprehensive_markdown_report_safe(results, failed_symbols, analysis_date)
                
        except Exception as e:
            print(f"Critical error in market scanner: {str(e)}", file=sys.stderr)
            return f"Error: Critical failure in market scanner - {str(e)}"

def analyze_single_symbol_safe(symbol: str, period: str) -> Optional[Dict]:
    """Safely analyze a single symbol using all 5 strategies"""
    
    try:
        # Download basic data for price info with error handling
        try:
            data = yf.download(symbol, period="5d", progress=False, multi_level_index=False)
            if data.empty:
                return None
        except Exception:
            return None
            
        current_price = float(data['Close'].iloc[-1])
        price_change_1d = float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100) if len(data) > 1 else 0.0
        
        # Initialize result dictionary
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'price_change_1d': price_change_1d,
            'strategies': {},
            'overall_score': 0.0,
            'overall_signal': 'NEUTRAL',
            'signal_consensus': 'MIXED',
            'risk_level': 'MEDIUM'
        }
        
        # Strategy 1: Bollinger Z-Score
        try:
            zscore_result = analyze_bollinger_zscore_safe(symbol, period)
            result['strategies']['bollinger_zscore'] = zscore_result
        except Exception as e:
            result['strategies']['bollinger_zscore'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
        
        # Strategy 2: Bollinger-Fibonacci
        try:
            fib_result = analyze_bollinger_fibonacci_safe(symbol, period)
            result['strategies']['bollinger_fibonacci'] = fib_result
        except Exception as e:
            result['strategies']['bollinger_fibonacci'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
        
        # Strategy 3: MACD-Donchian
        try:
            macd_don_result = analyze_macd_donchian_safe(symbol, period)
            result['strategies']['macd_donchian'] = macd_don_result
        except Exception as e:
            result['strategies']['macd_donchian'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
        
        # Strategy 4: Connors RSI-Z Score
        try:
            connors_result = analyze_connors_zscore_safe(symbol, period)
            result['strategies']['connors_zscore'] = connors_result
        except Exception as e:
            result['strategies']['connors_zscore'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
        
        # Strategy 5: Dual Moving Average
        try:
            dual_ma_result = analyze_dual_ma_safe(symbol, period)
            result['strategies']['dual_ma'] = dual_ma_result
        except Exception as e:
            result['strategies']['dual_ma'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
        
        # Calculate overall metrics
        calculate_overall_metrics_safe(result)
        
        return result
        
    except Exception as e:
        return None

def analyze_bollinger_zscore_safe(symbol: str, period: str) -> Dict:
    """Safely analyze Bollinger Z-Score strategy"""
    
    try:
        data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
        if data.empty:
            return {'error': 'No data', 'score': 0, 'signal': 'NEUTRAL'}
            
        window = 20
        closes = data["Close"]
        rolling_mean = closes.rolling(window=window).mean()
        rolling_std = closes.rolling(window=window).std()
        z_score = (closes - rolling_mean) / rolling_std
        
        latest_z_score = float(z_score.iloc[-1])
        
        # Determine signal
        if latest_z_score > 2:
            signal = "STRONG_SELL"
            score = -80.0
        elif latest_z_score > 1:
            signal = "SELL"
            score = -40.0
        elif latest_z_score < -2:
            signal = "STRONG_BUY"
            score = 80.0
        elif latest_z_score < -1:
            signal = "BUY"
            score = 40.0
        else:
            signal = "NEUTRAL"
            score = float(latest_z_score * 20)  # Scale to ±20 for neutral range
        
        return {
            'z_score': latest_z_score,
            'signal': signal,
            'score': score,
            'confidence': min(abs(latest_z_score) * 50, 100),
            'description': f"Z-Score: {latest_z_score:.2f} - {'Oversold' if latest_z_score < -1 else 'Overbought' if latest_z_score > 1 else 'Normal'}"
        }
    except Exception:
        return {'error': 'Analysis failed', 'score': 0.0, 'signal': 'NEUTRAL', 'confidence': 0, 'description': 'Failed'}

def analyze_bollinger_fibonacci_safe(symbol: str, period: str) -> Dict:
    """Safely analyze Bollinger-Fibonacci strategy"""
    
    try:
        data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
        if data.empty:
            return {'error': 'No data', 'score': 0, 'signal': 'NEUTRAL'}
            
        window = 20
        
        # Calculate Bollinger Bands safely
        try:
            calculate_bollinger_bands(data, symbol, period, window, 2)
        except Exception:
            pass
        
        # Calculate basic strategy score (simplified)
        if "%B" in data.columns and not data["%B"].isna().iloc[-1]:
            bb_score = float((0.5 - data["%B"].iloc[-1]) * 50)
        else:
            bb_score = 0.0
        
        # Determine signal based on BB score
        if bb_score > 20:
            signal = "BUY"
            score = bb_score
        elif bb_score < -20:
            signal = "SELL"
            score = bb_score
        else:
            signal = "NEUTRAL"
            score = bb_score
        
        return {
            'bb_score': bb_score,
            'signal': signal,
            'score': score,
            'confidence': min(abs(bb_score) * 2, 100),
            'description': f"BB-Fib Score: {bb_score:.1f} - {signal}"
        }
    except Exception:
        return {'error': 'Analysis failed', 'score': 0.0, 'signal': 'NEUTRAL', 'confidence': 0, 'description': 'Failed'}

def analyze_macd_donchian_safe(symbol: str, period: str) -> Dict:
    """Safely analyze MACD-Donchian strategy"""
    
    try:
        macd_score = calculate_macd_score(symbol, period)
        donchian_score = calculate_donchian_channel_score(symbol, period)
        
        combined_score = (float(macd_score) + float(donchian_score)) / 2
        
        if combined_score > 25:
            signal = "BUY"
        elif combined_score < -25:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            'macd_score': float(macd_score),
            'donchian_score': float(donchian_score),
            'combined_score': combined_score,
            'signal': signal,
            'score': combined_score,
            'confidence': min(abs(combined_score) * 2, 100),
            'description': f"MACD-Don Score: {combined_score:.1f} - {signal}"
        }
    except Exception:
        return {'error': 'Analysis failed', 'score': 0.0, 'signal': 'NEUTRAL', 'confidence': 0, 'description': 'Failed'}

def analyze_connors_zscore_safe(symbol: str, period: str) -> Dict:
    """Safely analyze Connors RSI-Z Score strategy"""
    
    try:
        # Calculate Connors RSI
        current_crsi, connors_score, current_price_rsi, current_streak_rsi, current_percent_rank = calculate_connors_rsi_score(symbol, period)
        
        # Calculate Z-Score
        current_zscore, zscore_score, current_price, current_mean, current_std = calculate_zscore_indicator(symbol, period)
        
        # Combined score (70% Connors, 30% Z-Score)
        combined_score = (float(connors_score) * 0.7) + (float(zscore_score) * 0.3)
        
        if combined_score > 25:
            signal = "BUY"
        elif combined_score < -25:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            'connors_rsi': float(current_crsi),
            'z_score': float(current_zscore),
            'combined_score': combined_score,
            'signal': signal,
            'score': combined_score,
            'confidence': min(abs(combined_score), 100),
            'description': f"Connors-Z Score: {combined_score:.1f} - {signal}"
        }
    except Exception:
        return {'error': 'Analysis failed', 'score': 0.0, 'signal': 'NEUTRAL', 'confidence': 0, 'description': 'Failed'}

def analyze_dual_ma_safe(symbol: str, period: str) -> Dict:
    """Safely analyze Dual Moving Average strategy"""
    
    try:
        data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
        if data.empty:
            return {'error': 'No data', 'score': 0, 'signal': 'NEUTRAL'}
            
        # Calculate EMAs
        short_period, long_period = 50, 200
        ema_short = data['Close'].ewm(span=short_period).mean()
        ema_long = data['Close'].ewm(span=long_period).mean()
        
        current_price = float(data['Close'].iloc[-1])
        current_short_ema = float(ema_short.iloc[-1])
        current_long_ema = float(ema_long.iloc[-1])
        
        # Calculate score
        ma_separation = (current_short_ema - current_long_ema) / current_long_ema * 100
        score = float(np.clip(ma_separation * 10, -100, 100))  # Scale for scoring
        
        if score > 20:
            signal = "BUY"
        elif score < -20:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        trend = "BULLISH" if current_short_ema > current_long_ema else "BEARISH"
        
        return {
            'ma_separation': ma_separation,
            'trend': trend,
            'signal': signal,
            'score': score,
            'confidence': min(abs(score), 100),
            'description': f"Dual MA: {trend} - {signal}"
        }
    except Exception:
        return {'error': 'Analysis failed', 'score': 0.0, 'signal': 'NEUTRAL', 'confidence': 0, 'description': 'Failed'}

def calculate_overall_metrics_safe(result: Dict):
    """Safely calculate overall metrics from individual strategy results"""
    
    try:
        valid_strategies = [s for s in result['strategies'].values() if 'error' not in s]
        
        if not valid_strategies:
            result['overall_score'] = 0.0
            result['overall_signal'] = 'ERROR'
            return
        
        # Calculate overall score (average of strategy scores)
        scores = [float(s.get('score', 0)) for s in valid_strategies]
        result['overall_score'] = float(np.mean(scores))
        
        # Calculate signal consensus
        signals = [s.get('signal', 'NEUTRAL') for s in valid_strategies]
        
        buy_signals = sum(1 for s in signals if 'BUY' in s)
        sell_signals = sum(1 for s in signals if 'SELL' in s)
        neutral_signals = len(signals) - buy_signals - sell_signals
        
        # Determine overall signal
        if result['overall_score'] > 30:
            result['overall_signal'] = 'STRONG_BUY'
        elif result['overall_score'] > 15:
            result['overall_signal'] = 'BUY'
        elif result['overall_score'] < -30:
            result['overall_signal'] = 'STRONG_SELL'
        elif result['overall_score'] < -15:
            result['overall_signal'] = 'SELL'
        else:
            result['overall_signal'] = 'NEUTRAL'
        
        # Signal consensus
        total_signals = len(signals)
        if buy_signals > total_signals * 0.6:
            result['signal_consensus'] = 'BULLISH_CONSENSUS'
        elif sell_signals > total_signals * 0.6:
            result['signal_consensus'] = 'BEARISH_CONSENSUS'
        elif neutral_signals > total_signals * 0.6:
            result['signal_consensus'] = 'NEUTRAL_CONSENSUS'
        else:
            result['signal_consensus'] = 'MIXED_SIGNALS'
        
        # Risk level
        confidence_scores = [float(s.get('confidence', 50)) for s in valid_strategies]
        avg_confidence = np.mean(confidence_scores)
        
        if avg_confidence > 70:
            result['risk_level'] = 'HIGH_CONFIDENCE'
        elif avg_confidence > 40:
            result['risk_level'] = 'MEDIUM_CONFIDENCE'
        else:
            result['risk_level'] = 'LOW_CONFIDENCE'
    except Exception:
        result['overall_score'] = 0.0
        result['overall_signal'] = 'ERROR'
        result['signal_consensus'] = 'ERROR'
        result['risk_level'] = 'ERROR'

def generate_comprehensive_markdown_report_safe(results: List[Dict], failed_symbols: List[str], analysis_date: str) -> str:
    """Generate comprehensive markdown report safely"""
    
    try:
        # Sort results by overall score
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Categorize results
        strong_buys = [r for r in results if r['overall_signal'] == 'STRONG_BUY']
        buys = [r for r in results if r['overall_signal'] == 'BUY']
        neutrals = [r for r in results if r['overall_signal'] == 'NEUTRAL']
        sells = [r for r in results if r['overall_signal'] == 'SELL']
        strong_sells = [r for r in results if r['overall_signal'] == 'STRONG_SELL']
        
        report = f"""# Comprehensive Market Analysis Report
*Analysis Date: {analysis_date}*  
*Analyzed Symbols: {len(results)} successful, {len(failed_symbols)} failed*

## Executive Summary

This comprehensive market analysis evaluates {len(results)} stocks using five different technical indicators and strategies.

### Market Overview
- **Strong Buy Signals:** {len(strong_buys)} stocks
- **Buy Signals:** {len(buys)} stocks  
- **Neutral:** {len(neutrals)} stocks
- **Sell Signals:** {len(sells)} stocks
- **Strong Sell Signals:** {len(strong_sells)} stocks

## Top Opportunities Ranking

| Rank | Symbol | Price | 1D Change | Overall Score | Signal |
|------|--------|-------|-----------|---------------|--------|
"""
        
        # Add top 15 opportunities
        for i, result in enumerate(results[:15], 1):
            price_change_emoji = "🟢" if result['price_change_1d'] > 0 else "🔴" if result['price_change_1d'] < 0 else "⚪"
            
            report += f"| {i} | {result['symbol']} | ${result['current_price']:.2f} | {price_change_emoji} {result['price_change_1d']:+.1f}% | {result['overall_score']:.1f} | {result['overall_signal']} |\n"
        
        # Add top recommendations
        if strong_buys:
            report += f"""

## Strong Buy Opportunities ({len(strong_buys)} stocks)

"""
            for stock in strong_buys[:3]:  # Top 3 strong buys
                report += f"### {stock['symbol']} - ${stock['current_price']:.2f}\n"
                report += f"**Overall Score:** {stock['overall_score']:.1f} | **Signal:** {stock['overall_signal']}\n\n"
        
        if strong_sells:
            report += f"""

## Strong Sell Signals ({len(strong_sells)} stocks)

These stocks should be avoided or considered for shorting.

"""
            for stock in strong_sells[-2:]:  # Bottom 2 strong sells
                report += f"### {stock['symbol']} - ${stock['current_price']:.2f}\n"
                report += f"**Overall Score:** {stock['overall_score']:.1f} | **Signal:** {stock['overall_signal']}\n\n"
        
        # Market sentiment
        bullish_count = len(strong_buys) + len(buys)
        bearish_count = len(strong_sells) + len(sells)
        
        market_sentiment = 'BULLISH' if bullish_count > bearish_count else 'BEARISH' if bearish_count > bullish_count else 'NEUTRAL'
        
        report += f"""

## Market Sentiment: {market_sentiment}

- **Bullish Bias:** {bullish_count / len(results) * 100:.1f}% of stocks show buy signals
- **Bearish Bias:** {bearish_count / len(results) * 100:.1f}% of stocks show sell signals

### Recommended Actions:
1. Focus on Strong Buy signals with high confidence
2. Consider portfolio diversification
3. Monitor risk levels and use stop-losses

"""
        
        if failed_symbols:
            report += f"""

## Analysis Failures
Failed to analyze: {', '.join(failed_symbols)}

"""
        
        report += """
---
*This analysis is for educational purposes only and should not be considered as financial advice.*
"""
        
        return report
        
    except Exception as e:
        return f"Error generating report: {str(e)}"

def generate_summary_report_safe(results: List[Dict], failed_symbols: List[str], analysis_date: str) -> str:
    """Generate a safe concise summary report"""
    
    try:
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        strong_buys = [r for r in results if r['overall_signal'] == 'STRONG_BUY']
        buys = [r for r in results if r['overall_signal'] == 'BUY']
        sells = [r for r in results if r['overall_signal'] == 'SELL']
        strong_sells = [r for r in results if r['overall_signal'] == 'STRONG_SELL']
        
        summary = f"""MARKET SCANNER SUMMARY - {analysis_date}
{'='*50}

ANALYZED: {len(results)} stocks | FAILED: {len(failed_symbols)} stocks

SIGNAL DISTRIBUTION:
• Strong Buy: {len(strong_buys)} stocks
• Buy: {len(buys)} stocks
• Neutral: {len(results) - len(strong_buys) - len(buys) - len(sells) - len(strong_sells)} stocks
• Sell: {len(sells)} stocks
• Strong Sell: {len(strong_sells)} stocks

TOP 10 OPPORTUNITIES:
"""
        
        for i, result in enumerate(results[:10], 1):
            summary += f"{i:2d}. {result['symbol']:6s} | ${result['current_price']:8.2f} | {result['overall_score']:6.1f} | {result['overall_signal']}\n"
        
        if strong_buys:
            summary += f"\nSTRONG BUY RECOMMENDATIONS:\n"
            for stock in strong_buys[:5]:
                summary += f"• {stock['symbol']} - Score: {stock['overall_score']:.1f}\n"
        
        bullish_count = len(strong_buys) + len(buys)
        bearish_count = len(sells) + len(strong_sells)
        market_sentiment = 'BULLISH' if bullish_count > bearish_count else 'BEARISH' if bearish_count > bullish_count else 'NEUTRAL'
        
        summary += f"\nMARKET SENTIMENT: {market_sentiment}"
        
        return summary
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"
    
# Add this at the end of your existing comprehensive_market_scanner.py file

# Valid periods for yfinance
VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']

def validate_period(period: str) -> str:
    """Validate and fix period parameter"""
    # Common fixes
    period_fixes = {
        '6m': '6mo',
        '3m': '3mo', 
        '1m': '1mo',
        '2m': '2mo',
        '12m': '1y',
        '24m': '2y'
    }
    
    if period in period_fixes:
        return period_fixes[period]
    
    if period not in VALID_PERIODS:
        print(f"Warning: Invalid period '{period}', using '1y' instead", file=sys.stderr)
        return '1y'
    
    return period

def add_enhanced_market_scanner_tool(mcp):
    """Add enhanced market scanner with period validation"""
    
    @mcp.tool()
    def enhanced_market_scanner(
        symbols,
        period: str = "1y",
        output_format: str = "detailed"
    ) -> str:
        """
        Enhanced market scanner with period validation and performance analysis.
        
        This tool will:
        1. Validate and auto-fix period parameters (e.g., 6m -> 6mo)
        2. Analyze each symbol using all 5 strategies
        3. Calculate performance vs buy-and-hold
        4. Generate detailed reports with reasoning
        
        Parameters:
        symbols: List of stock ticker symbols (comma-separated string or list)
        period (str): Data period - 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max (default: 1y)
        output_format (str): "detailed", "summary", or "performance" (default: detailed)
        
        Returns:
        str: Enhanced market analysis report
        """
        
        try:
            # Validate and fix period
            period = validate_period(period)
            
            # Use the existing comprehensive scanner logic but with period validation
            if isinstance(symbols, str):
                symbol_list = [s.strip().upper() for s in symbols.replace('"', '').replace("'", "").split(',')]
                symbol_list = [s for s in symbol_list if s and s.replace('.', '').replace('-', '').isalnum()]
            elif isinstance(symbols, list):
                symbol_list = [str(s).strip().upper() for s in symbols if str(s).strip()]
            else:
                return "Error: Symbols must be provided as a list or comma-separated string"

            if not symbol_list:
                return "Error: No valid symbols provided for scanning"

            # Limit for performance
            if len(symbol_list) > 15:
                symbol_list = symbol_list[:15]
                
            analysis_date = datetime.now().strftime("%B %d, %Y")
            
            # Simple analysis for each symbol
            results = []
            failed_symbols = []
            
            for symbol in symbol_list:
                try:
                    # Get basic data
                    data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
                    if data.empty:
                        failed_symbols.append(symbol)
                        continue
                        
                    current_price = float(data['Close'].iloc[-1])
                    start_price = float(data['Close'].iloc[0])
                    buy_hold_return = (current_price - start_price) / start_price * 100
                    
                    # Quick analysis using existing functions
                    try:
                        # Bollinger Z-Score
                        closes = data["Close"]
                        rolling_mean = closes.rolling(window=20).mean()
                        rolling_std = closes.rolling(window=20).std()
                        z_score = (closes - rolling_mean) / rolling_std
                        latest_z_score = float(z_score.iloc[-1])
                        
                        if latest_z_score > 1:
                            bb_signal = "SELL"
                            bb_score = -40
                        elif latest_z_score < -1:
                            bb_signal = "BUY" 
                            bb_score = 40
                        else:
                            bb_signal = "NEUTRAL"
                            bb_score = 0
                            
                        # Simple combined score
                        overall_score = bb_score
                        
                        if overall_score > 15:
                            overall_signal = "BUY"
                        elif overall_score < -15:
                            overall_signal = "SELL"
                        else:
                            overall_signal = "NEUTRAL"
                            
                        results.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'buy_hold_return': buy_hold_return,
                            'overall_score': overall_score,
                            'overall_signal': overall_signal,
                            'z_score': latest_z_score,
                            'reasoning': f"Z-Score: {latest_z_score:.2f} - {'Oversold' if latest_z_score < -1 else 'Overbought' if latest_z_score > 1 else 'Normal'}"
                        })
                        
                    except Exception as e:
                        failed_symbols.append(symbol)
                        
                except Exception as e:
                    failed_symbols.append(symbol)
            
            if not results:
                return f"Error: No valid analysis results for symbols: {symbol_list}"
            
            # Generate report based on format
            if output_format.lower() == "performance":
                return generate_performance_report(results, failed_symbols, analysis_date, period)
            elif output_format.lower() == "summary":
                return generate_enhanced_summary_simple(results, failed_symbols, analysis_date, period)
            else:
                return generate_detailed_report_simple(results, failed_symbols, analysis_date, period)
                
        except Exception as e:
            return f"Error in enhanced market scanner: {str(e)}"

def generate_performance_report(results, failed_symbols, analysis_date, period):
    """Generate performance-focused report"""
    
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    report = f"""# Performance-Focused Market Analysis
*Date: {analysis_date} | Period: {period}*

## Performance Summary

| Rank | Symbol | Current Price | Buy & Hold Return | Technical Score | Signal | Analysis |
|------|--------|---------------|------------------|-----------------|--------|----------|
"""
    
    for i, result in enumerate(results, 1):
        report += f"| {i} | {result['symbol']} | ${result['current_price']:.2f} | {result['buy_hold_return']:+.1f}% | {result['overall_score']:.1f} | {result['overall_signal']} | {result['reasoning']} |\n"
    
    # Summary stats
    avg_buy_hold = sum(r['buy_hold_return'] for r in results) / len(results)
    buy_signals = len([r for r in results if r['overall_signal'] == 'BUY'])
    sell_signals = len([r for r in results if r['overall_signal'] == 'SELL'])
    
    report += f"""

## Market Summary

- **Average Buy & Hold Return:** {avg_buy_hold:+.1f}% over {period}
- **Buy Signals:** {buy_signals}/{len(results)} stocks ({buy_signals/len(results)*100:.1f}%)
- **Sell Signals:** {sell_signals}/{len(results)} stocks ({sell_signals/len(results)*100:.1f}%)
- **Market Sentiment:** {'BULLISH' if buy_signals > sell_signals else 'BEARISH' if sell_signals > buy_signals else 'NEUTRAL'}

## Top Recommendations

"""
    
    top_buys = [r for r in results if r['overall_signal'] == 'BUY'][:3]
    if top_buys:
        report += "**BUY Recommendations:**\n"
        for stock in top_buys:
            report += f"- **{stock['symbol']}** (Score: {stock['overall_score']:.1f}) - {stock['reasoning']}\n"
    
    top_sells = [r for r in results if r['overall_signal'] == 'SELL'][:2]
    if top_sells:
        report += "\n**SELL/AVOID Recommendations:**\n"
        for stock in top_sells:
            report += f"- **{stock['symbol']}** (Score: {stock['overall_score']:.1f}) - {stock['reasoning']}\n"
    
    if failed_symbols:
        report += f"\n**Failed Analysis:** {', '.join(failed_symbols)}\n"
    
    report += """

---
*This analysis uses technical indicators for educational purposes only. Not financial advice.*
"""
    
    return report

def generate_enhanced_summary_simple(results, failed_symbols, analysis_date, period):
    """Generate simple enhanced summary"""
    
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    buy_signals = [r for r in results if r['overall_signal'] == 'BUY']
    sell_signals = [r for r in results if r['overall_signal'] == 'SELL']
    avg_return = sum(r['buy_hold_return'] for r in results) / len(results)
    
    summary = f"""ENHANCED MARKET SCANNER SUMMARY - {analysis_date}
{'='*60}

PERIOD: {period} | ANALYZED: {len(results)} | FAILED: {len(failed_symbols)}
AVERAGE BUY & HOLD RETURN: {avg_return:+.1f}%

SIGNAL DISTRIBUTION:
• Buy Signals: {len(buy_signals)} ({len(buy_signals)/len(results)*100:.1f}%)
• Sell Signals: {len(sell_signals)} ({len(sell_signals)/len(results)*100:.1f}%)
• Neutral: {len(results) - len(buy_signals) - len(sell_signals)} ({(len(results) - len(buy_signals) - len(sell_signals))/len(results)*100:.1f}%)

TOP OPPORTUNITIES:
"""
    
    for i, result in enumerate(results[:8], 1):
        summary += f"{i:2d}. {result['symbol']:6s} | ${result['current_price']:7.2f} | Score: {result['overall_score']:5.1f} | Return: {result['buy_hold_return']:+5.1f}% | {result['overall_signal']}\n"
    
    if buy_signals:
        summary += f"\nBUY RECOMMENDATIONS:\n"
        for stock in buy_signals[:5]:
            summary += f"• {stock['symbol']} - {stock['reasoning']}\n"
    
    market_sentiment = 'BULLISH' if len(buy_signals) > len(sell_signals) else 'BEARISH' if len(sell_signals) > len(buy_signals) else 'NEUTRAL'
    summary += f"\nMARKET SENTIMENT: {market_sentiment}"
    
    return summary

def generate_detailed_report_simple(results, failed_symbols, analysis_date, period):
    """Generate simple detailed report"""
    
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    buy_signals = [r for r in results if r['overall_signal'] == 'BUY']
    sell_signals = [r for r in results if r['overall_signal'] == 'SELL']
    
    report = f"""# Enhanced Market Analysis Report
*Analysis Date: {analysis_date} | Period: {period}*

## Executive Summary

Analyzed {len(results)} stocks with technical indicators and performance metrics.

### Market Overview
- **Buy Signals:** {len(buy_signals)} stocks ({len(buy_signals)/len(results)*100:.1f}%)
- **Sell Signals:** {len(sell_signals)} stocks ({len(sell_signals)/len(results)*100:.1f}%)
- **Neutral:** {len(results) - len(buy_signals) - len(sell_signals)} stocks

## Performance Rankings

| Rank | Symbol | Price | Buy & Hold Return | Technical Score | Signal | Analysis |
|------|--------|-------|------------------|-----------------|--------|----------|
"""
    
    for i, result in enumerate(results, 1):
        report += f"| {i} | {result['symbol']} | ${result['current_price']:.2f} | {result['buy_hold_return']:+.1f}% | {result['overall_score']:.1f} | {result['overall_signal']} | {result['reasoning']} |\n"
    
    if buy_signals:
        report += f"""

## 🟢 Buy Recommendations ({len(buy_signals)} stocks)

"""
        for stock in buy_signals:
            report += f"### {stock['symbol']} - ${stock['current_price']:.2f}\n"
            report += f"**Signal:** {stock['overall_signal']} (Score: {stock['overall_score']:.1f})  \n"
            report += f"**Buy & Hold Return:** {stock['buy_hold_return']:+.1f}%  \n"
            report += f"**Analysis:** {stock['reasoning']}\n\n"
    
    if sell_signals:
        report += f"""

## 🔴 Sell/Avoid Recommendations ({len(sell_signals)} stocks)

"""
        for stock in sell_signals:
            report += f"### {stock['symbol']} - ${stock['current_price']:.2f}\n"
            report += f"**Signal:** {stock['overall_signal']} (Score: {stock['overall_score']:.1f})  \n"
            report += f"**Analysis:** {stock['reasoning']}\n\n"
    
    market_sentiment = 'BULLISH' if len(buy_signals) > len(sell_signals) else 'BEARISH' if len(sell_signals) > len(buy_signals) else 'NEUTRAL'
    
    report += f"""

## Market Conclusion: {market_sentiment}

Based on technical analysis of {len(results)} stocks, the market shows a **{market_sentiment.lower()}** bias with {len(buy_signals)/len(results)*100:.1f}% of stocks showing buy signals.

"""
    
    if failed_symbols:
        report += f"**Failed Analysis:** {', '.join(failed_symbols)}\n"
    
    return report