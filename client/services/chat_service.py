# Complete Enhanced services/chat_service.py with Advanced Processing Time Features and Service Enhancements

import streamlit as st
from config import SERVER_CONFIG
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any, Optional, Tuple
from services.mcp_service import disconnect_from_mcp_servers
from utils.async_helpers import run_async
from langchain.schema import SystemMessage
from datetime import datetime, timedelta
import logging
import time
import statistics
import json
import threading
from collections import deque, defaultdict

# Advanced Performance Monitoring Classes
class PerformanceMonitor:
    """Advanced performance monitor with comprehensive analytics and real-time tracking."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.reset_metrics()
        self._lock = threading.Lock()  # Thread safety for concurrent access
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        with self._lock:
            self.processing_times = deque(maxlen=self.max_history)
            self.tool_execution_times = deque(maxlen=self.max_history)
            self.token_usage = deque(maxlen=self.max_history)
            self.error_log = deque(maxlen=100)  # Keep last 100 errors
            self.session_start = time.time()
            self.total_messages = 0
            self.total_tokens_estimated = 0
            self.total_tool_executions = 0
            self.successful_messages = 0
            self.failed_messages = 0
            self.performance_buckets = {
                'fast': 0,    # < 2 seconds
                'medium': 0,  # 2-5 seconds  
                'slow': 0,    # 5-10 seconds
                'very_slow': 0  # > 10 seconds
            }
            self.hourly_stats = defaultdict(list)  # Performance by hour
            self.tool_performance = defaultdict(list)  # Performance by tool
    
    def record_processing_time(self, processing_time: float, message_length: int = 0, 
                             token_count: Optional[int] = None, error_occurred: bool = False,
                             tool_used: Optional[str] = None):
        """Record a comprehensive processing time measurement."""
        with self._lock:
            # Basic metrics
            self.processing_times.append({
                'time': processing_time,
                'timestamp': time.time(),
                'message_length': message_length,
                'token_count': token_count or (message_length // 4),
                'error': error_occurred,
                'tool_used': tool_used
            })
            
            self.total_messages += 1
            if error_occurred:
                self.failed_messages += 1
            else:
                self.successful_messages += 1
            
            if token_count:
                self.total_tokens_estimated += token_count
            else:
                self.total_tokens_estimated += message_length // 4
            
            # Performance bucketing
            if processing_time < 2:
                self.performance_buckets['fast'] += 1
            elif processing_time < 5:
                self.performance_buckets['medium'] += 1
            elif processing_time < 10:
                self.performance_buckets['slow'] += 1
            else:
                self.performance_buckets['very_slow'] += 1
            
            # Hourly statistics
            current_hour = datetime.now().hour
            self.hourly_stats[current_hour].append(processing_time)
            
            # Tool-specific performance
            if tool_used:
                self.tool_performance[tool_used].append(processing_time)
    
    def record_tool_execution(self, tool_name: str, execution_time: float, 
                            success: bool = True, error_msg: str = None):
        """Record detailed tool execution metrics."""
        with self._lock:
            execution_record = {
                'tool_name': tool_name,
                'execution_time': execution_time,
                'timestamp': time.time(),
                'success': success,
                'error_msg': error_msg
            }
            
            self.tool_execution_times.append(execution_record)
            self.total_tool_executions += 1
            
            if not success and error_msg:
                self.error_log.append({
                    'type': 'tool_execution',
                    'tool_name': tool_name,
                    'error': error_msg,
                    'timestamp': time.time()
                })
    
    def record_error(self, error_type: str, error_msg: str, context: Dict = None):
        """Record detailed error information."""
        with self._lock:
            self.error_log.append({
                'type': error_type,
                'error': error_msg,
                'context': context or {},
                'timestamp': time.time()
            })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary with advanced analytics."""
        with self._lock:
            if not self.processing_times:
                return {'status': 'no_data'}
            
            # Extract processing times
            times = [record['time'] for record in self.processing_times]
            session_duration = time.time() - self.session_start
            
            # Calculate advanced statistics
            percentiles = self._calculate_percentiles(times)
            trends = self._calculate_trends()
            efficiency_metrics = self._calculate_efficiency_metrics()
            
            return {
                'status': 'active',
                'session_duration_minutes': session_duration / 60,
                'total_messages': self.total_messages,
                'successful_messages': self.successful_messages,
                'failed_messages': self.failed_messages,
                'success_rate': (self.successful_messages / max(self.total_messages, 1)) * 100,
                
                # Time statistics
                'total_processing_time': sum(times),
                'average_processing_time': statistics.mean(times),
                'median_processing_time': statistics.median(times),
                'min_processing_time': min(times),
                'max_processing_time': max(times),
                'std_dev_processing_time': statistics.stdev(times) if len(times) > 1 else 0,
                
                # Percentiles
                'percentiles': percentiles,
                
                # Performance distribution
                'performance_buckets': dict(self.performance_buckets),
                'performance_percentages': self._calculate_bucket_percentages(),
                
                # Efficiency metrics
                'messages_per_minute': (self.total_messages / max(session_duration / 60, 1)),
                'tokens_per_second': efficiency_metrics['tokens_per_second'],
                'average_tokens_per_message': efficiency_metrics['avg_tokens_per_message'],
                
                # Tool statistics
                'total_tool_executions': self.total_tool_executions,
                'tool_success_rate': self._calculate_tool_success_rate(),
                'most_used_tools': self._get_most_used_tools(),
                
                # Advanced metrics
                'performance_grade': self._calculate_performance_grade(),
                'efficiency_score': efficiency_metrics['efficiency_score'],
                'reliability_score': self._calculate_reliability_score(),
                'trends': trends,
                'hourly_performance': self._get_hourly_performance(),
                
                # Error analysis
                'error_rate': (len(self.error_log) / max(self.total_messages, 1)) * 100,
                'recent_errors': list(self.error_log)[-5:] if self.error_log else [],
                'error_types': self._analyze_error_types()
            }
    
    def _calculate_percentiles(self, times: List[float]) -> Dict[str, float]:
        """Calculate performance percentiles."""
        if len(times) < 2:
            return {}
        
        try:
            import numpy as np
            return {
                'p25': float(np.percentile(times, 25)),
                'p50': float(np.percentile(times, 50)),  # median
                'p75': float(np.percentile(times, 75)),
                'p90': float(np.percentile(times, 90)),
                'p95': float(np.percentile(times, 95)),
                'p99': float(np.percentile(times, 99))
            }
        except ImportError:
            # Fallback without numpy
            sorted_times = sorted(times)
            n = len(sorted_times)
            return {
                'p25': sorted_times[int(0.25 * n)],
                'p50': sorted_times[int(0.50 * n)],
                'p75': sorted_times[int(0.75 * n)],
                'p90': sorted_times[int(0.90 * n)],
                'p95': sorted_times[int(0.95 * n)],
                'p99': sorted_times[int(0.99 * n)]
            }
    
    def _calculate_bucket_percentages(self) -> Dict[str, float]:
        """Calculate performance bucket percentages."""
        total = sum(self.performance_buckets.values())
        if total == 0:
            return {k: 0.0 for k in self.performance_buckets.keys()}
        
        return {
            k: (v / total) * 100 
            for k, v in self.performance_buckets.items()
        }
    
    def _calculate_efficiency_metrics(self) -> Dict[str, float]:
        """Calculate advanced efficiency metrics."""
        session_duration = time.time() - self.session_start
        
        tokens_per_second = self.total_tokens_estimated / max(session_duration, 1)
        avg_tokens_per_message = self.total_tokens_estimated / max(self.total_messages, 1)
        
        # Efficiency score based on multiple factors
        time_efficiency = min(100, (2.0 / max(statistics.mean([r['time'] for r in self.processing_times]), 0.1)) * 100)
        token_efficiency = min(100, tokens_per_second * 10)  # Scale appropriately
        success_efficiency = (self.successful_messages / max(self.total_messages, 1)) * 100
        
        efficiency_score = (time_efficiency + token_efficiency + success_efficiency) / 3
        
        return {
            'tokens_per_second': tokens_per_second,
            'avg_tokens_per_message': avg_tokens_per_message,
            'efficiency_score': efficiency_score
        }
    
    def _calculate_performance_grade(self) -> str:
        """Calculate overall performance grade with advanced criteria."""
        if not self.processing_times:
            return 'N/A'
        
        times = [record['time'] for record in self.processing_times]
        avg_time = statistics.mean(times)
        success_rate = (self.successful_messages / max(self.total_messages, 1)) * 100
        
        # Advanced grading criteria
        if avg_time < 1.5 and success_rate >= 95:
            return 'A+'
        elif avg_time < 2.0 and success_rate >= 90:
            return 'A'
        elif avg_time < 3.0 and success_rate >= 85:
            return 'B+'
        elif avg_time < 5.0 and success_rate >= 80:
            return 'B'
        elif avg_time < 7.0 and success_rate >= 70:
            return 'C'
        elif avg_time < 10.0 and success_rate >= 60:
            return 'D'
        else:
            return 'F'
    
    def _calculate_reliability_score(self) -> float:
        """Calculate system reliability score."""
        if self.total_messages == 0:
            return 100.0
        
        success_rate = (self.successful_messages / self.total_messages) * 100
        error_rate = (len(self.error_log) / self.total_messages) * 100
        
        # Factor in consistency (low standard deviation is good)
        times = [record['time'] for record in self.processing_times]
        if len(times) > 1:
            consistency_factor = max(0, 100 - (statistics.stdev(times) * 10))
        else:
            consistency_factor = 100
        
        reliability_score = (success_rate * 0.5) + ((100 - error_rate) * 0.3) + (consistency_factor * 0.2)
        return min(100, max(0, reliability_score))
    
    def _calculate_trends(self, window_size: int = 10) -> Dict[str, Any]:
        """Calculate performance trends with multiple window sizes."""
        if len(self.processing_times) < window_size:
            return {'status': 'insufficient_data'}
        
        times = [record['time'] for record in self.processing_times]
        
        # Short-term trend (last 10 messages)
        recent_times = times[-window_size:]
        older_times = times[-window_size*2:-window_size] if len(times) >= window_size*2 else times[:-window_size]
        
        trends = {}
        
        if older_times:
            recent_avg = statistics.mean(recent_times)
            older_avg = statistics.mean(older_times)
            
            trend_direction = 'improving' if recent_avg < older_avg else 'declining' if recent_avg > older_avg else 'stable'
            trend_magnitude = abs((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
            
            trends['short_term'] = {
                'direction': trend_direction,
                'magnitude_percent': trend_magnitude,
                'recent_average': recent_avg,
                'previous_average': older_avg
            }
        
        # Long-term trend (session-wide)
        if len(times) >= 20:
            first_quarter = times[:len(times)//4]
            last_quarter = times[-len(times)//4:]
            
            first_avg = statistics.mean(first_quarter)
            last_avg = statistics.mean(last_quarter)
            
            long_trend_direction = 'improving' if last_avg < first_avg else 'declining' if last_avg > first_avg else 'stable'
            long_trend_magnitude = abs((last_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
            
            trends['long_term'] = {
                'direction': long_trend_direction,
                'magnitude_percent': long_trend_magnitude,
                'session_start_average': first_avg,
                'session_end_average': last_avg
            }
        
        return trends
    
    def _get_hourly_performance(self) -> Dict[int, Dict[str, float]]:
        """Get performance statistics by hour."""
        hourly_perf = {}
        
        for hour, times in self.hourly_stats.items():
            if times:
                hourly_perf[hour] = {
                    'average': statistics.mean(times),
                    'median': statistics.median(times),
                    'count': len(times),
                    'min': min(times),
                    'max': max(times)
                }
        
        return hourly_perf
    
    def _calculate_tool_success_rate(self) -> float:
        """Calculate tool execution success rate."""
        if not self.tool_execution_times:
            return 100.0
        
        successful = sum(1 for record in self.tool_execution_times if record['success'])
        return (successful / len(self.tool_execution_times)) * 100
    
    def _get_most_used_tools(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently used tools with performance metrics."""
        tool_stats = defaultdict(lambda: {'count': 0, 'times': [], 'successes': 0})
        
        for record in self.tool_execution_times:
            tool_name = record['tool_name']
            tool_stats[tool_name]['count'] += 1
            tool_stats[tool_name]['times'].append(record['execution_time'])
            if record['success']:
                tool_stats[tool_name]['successes'] += 1
        
        # Convert to sorted list
        tool_list = []
        for tool_name, stats in tool_stats.items():
            if stats['times']:
                tool_list.append({
                    'tool_name': tool_name,
                    'usage_count': stats['count'],
                    'average_time': statistics.mean(stats['times']),
                    'success_rate': (stats['successes'] / stats['count']) * 100,
                    'total_time': sum(stats['times'])
                })
        
        return sorted(tool_list, key=lambda x: x['usage_count'], reverse=True)[:limit]
    
    def _analyze_error_types(self) -> Dict[str, int]:
        """Analyze and categorize error types."""
        error_types = defaultdict(int)
        
        for error in self.error_log:
            error_types[error['type']] += 1
        
        return dict(error_types)
    
    def get_performance_trends(self, window_size: int = 5) -> Dict[str, Any]:
        """Get detailed performance trends analysis."""
        return self._calculate_trends(window_size)
    
    def get_tool_performance_analysis(self) -> Dict[str, Any]:
        """Get detailed tool performance analysis."""
        if not self.tool_execution_times:
            return {'status': 'no_tool_data'}
        
        tool_analysis = {}
        tool_stats = defaultdict(lambda: {'times': [], 'successes': 0, 'failures': 0})
        
        for record in self.tool_execution_times:
            tool_name = record['tool_name']
            tool_stats[tool_name]['times'].append(record['execution_time'])
            if record['success']:
                tool_stats[tool_name]['successes'] += 1
            else:
                tool_stats[tool_name]['failures'] += 1
        
        for tool_name, stats in tool_stats.items():
            if stats['times']:
                total_executions = len(stats['times'])
                tool_analysis[tool_name] = {
                    'total_executions': total_executions,
                    'average_time': statistics.mean(stats['times']),
                    'median_time': statistics.median(stats['times']),
                    'min_time': min(stats['times']),
                    'max_time': max(stats['times']),
                    'success_rate': (stats['successes'] / total_executions) * 100,
                    'total_time': sum(stats['times']),
                    'std_dev': statistics.stdev(stats['times']) if len(stats['times']) > 1 else 0
                }
        
        return {
            'status': 'success',
            'tools': tool_analysis,
            'summary': {
                'total_tools_used': len(tool_analysis),
                'total_executions': len(self.tool_execution_times),
                'overall_success_rate': self._calculate_tool_success_rate()
            }
        }

class ChatPerformanceAnalyzer:
    """Advanced chat performance analyzer with predictive capabilities."""
    
    def __init__(self):
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def analyze_chat_performance(self, username: str) -> Dict[str, Any]:
        """Perform comprehensive chat performance analysis."""
        cache_key = f"chat_analysis_{username}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.analysis_cache:
            cached_data, timestamp = self.analysis_cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                return cached_data
        
        # Perform analysis
        analysis = self._perform_detailed_analysis(username)
        
        # Cache results
        self.analysis_cache[cache_key] = (analysis, current_time)
        
        return analysis
    
    def _perform_detailed_analysis(self, username: str) -> Dict[str, Any]:
        """Perform detailed performance analysis."""
        user_messages_key = f"user_{username}_messages"
        messages = st.session_state.get(user_messages_key, [])
        
        if not messages:
            return {'status': 'no_data'}
        
        # Extract performance data
        performance_data = []
        for msg in messages:
            if msg.get('processing_time') and msg.get('role') == 'assistant':
                performance_data.append({
                    'processing_time': msg['processing_time'],
                    'content_length': len(msg.get('content', '')),
                    'timestamp': msg.get('timestamp'),
                    'is_error': msg.get('is_error', False),
                    'tool_used': msg.get('tool_name') if msg.get('role') == 'tool' else None
                })
        
        if not performance_data:
            return {'status': 'no_performance_data'}
        
        # Perform various analyses
        time_analysis = self._analyze_response_times(performance_data)
        pattern_analysis = self._analyze_usage_patterns(performance_data)
        prediction_analysis = self._predict_performance_trends(performance_data)
        
        return {
            'status': 'success',
            'username': username,
            'analysis_timestamp': datetime.now().isoformat(),
            'message_count': len(messages),
            'performance_message_count': len(performance_data),
            'time_analysis': time_analysis,
            'pattern_analysis': pattern_analysis,
            'prediction_analysis': prediction_analysis,
            'recommendations': self._generate_recommendations(time_analysis, pattern_analysis)
        }
    
    def _analyze_response_times(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """Analyze response time patterns."""
        times = [d['processing_time'] for d in performance_data]
        
        # Basic statistics
        analysis = {
            'count': len(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times),
            'range': max(times) - min(times)
        }
        
        # Performance categories
        fast_count = sum(1 for t in times if t < 2)
        medium_count = sum(1 for t in times if 2 <= t < 5)
        slow_count = sum(1 for t in times if t >= 5)
        
        analysis['categories'] = {
            'fast': {'count': fast_count, 'percentage': (fast_count / len(times)) * 100},
            'medium': {'count': medium_count, 'percentage': (medium_count / len(times)) * 100},
            'slow': {'count': slow_count, 'percentage': (slow_count / len(times)) * 100}
        }
        
        # Outlier detection
        if len(times) > 2:
            q1 = statistics.median(sorted(times)[:len(times)//2])
            q3 = statistics.median(sorted(times)[len(times)//2:])
            iqr = q3 - q1
            outlier_threshold = q3 + 1.5 * iqr
            outliers = [t for t in times if t > outlier_threshold]
            
            analysis['outliers'] = {
                'count': len(outliers),
                'threshold': outlier_threshold,
                'values': outliers
            }
        
        return analysis
    
    def _analyze_usage_patterns(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """Analyze usage patterns and correlations."""
        # Time-based patterns
        hourly_performance = defaultdict(list)
        
        for data in performance_data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                hour = timestamp.hour
                hourly_performance[hour].append(data['processing_time'])
            except:
                continue
        
        # Content length correlation
        content_lengths = [d['content_length'] for d in performance_data]
        processing_times = [d['processing_time'] for d in performance_data]
        
        correlation = self._calculate_correlation(content_lengths, processing_times)
        
        # Error analysis
        error_count = sum(1 for d in performance_data if d.get('is_error'))
        error_rate = (error_count / len(performance_data)) * 100
        
        return {
            'hourly_patterns': {
                hour: {
                    'average': statistics.mean(times),
                    'count': len(times)
                } for hour, times in hourly_performance.items() if times
            },
            'content_correlation': {
                'correlation_coefficient': correlation,
                'interpretation': self._interpret_correlation(correlation)
            },
            'error_analysis': {
                'error_rate': error_rate,
                'error_count': error_count,
                'success_rate': 100 - error_rate
            }
        }
    
    def _predict_performance_trends(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """Predict future performance trends."""
        if len(performance_data) < 5:
            return {'status': 'insufficient_data'}
        
        times = [d['processing_time'] for d in performance_data]
        
        # Simple linear trend prediction
        try:
            import numpy as np
            x = np.arange(len(times))
            coefficients = np.polyfit(x, times, 1)
            slope = coefficients[0]
            
            # Predict next 5 messages
            future_x = np.arange(len(times), len(times) + 5)
            predictions = np.polyval(coefficients, future_x)
            
            trend_direction = 'improving' if slope < 0 else 'declining' if slope > 0 else 'stable'
            
            return {
                'status': 'success',
                'trend_direction': trend_direction,
                'slope': float(slope),
                'predictions': [float(p) for p in predictions],
                'confidence': 'low' if abs(slope) < 0.01 else 'medium' if abs(slope) < 0.1 else 'high'
            }
        except ImportError:
            # Fallback without numpy
            recent_avg = statistics.mean(times[-3:])
            overall_avg = statistics.mean(times)
            
            if recent_avg < overall_avg * 0.9:
                trend_direction = 'improving'
            elif recent_avg > overall_avg * 1.1:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
            
            return {
                'status': 'success',
                'trend_direction': trend_direction,
                'recent_average': recent_avg,
                'overall_average': overall_avg
            }
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient between two variables."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            import numpy as np
            return float(np.corrcoef(x, y)[0, 1])
        except ImportError:
            # Simple correlation calculation
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(a * b for a, b in zip(x, y))
            sum_x2 = sum(a * a for a in x)
            sum_y2 = sum(a * a for a in y)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
            
            return numerator / denominator if denominator != 0 else 0.0
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient."""
        abs_corr = abs(correlation)
        
        if abs_corr < 0.1:
            return "No correlation"
        elif abs_corr < 0.3:
            return "Weak correlation"
        elif abs_corr < 0.7:
            return "Moderate correlation"
        else:
            return "Strong correlation"
    
    def _generate_recommendations(self, time_analysis: Dict, pattern_analysis: Dict) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Response time recommendations
        avg_time = time_analysis.get('mean', 0)
        if avg_time > 5:
            recommendations.append("🐌 Consider breaking complex queries into smaller parts to improve response times")
        elif avg_time > 3:
            recommendations.append("⚡ Try to be more specific in your queries to reduce processing time")
        elif avg_time < 2:
            recommendations.append("✅ Excellent response times! Keep up the efficient querying")
        
        # Error rate recommendations
        error_rate = pattern_analysis.get('error_analysis', {}).get('error_rate', 0)
        if error_rate > 15:
            recommendations.append("🚨 High error rate detected. Double-check query syntax and table names")
        elif error_rate > 5:
            recommendations.append("⚠️ Consider using schema exploration tools before complex queries")
        elif error_rate < 2:
            recommendations.append("✅ Low error rate - excellent query quality!")
        
        # Content correlation recommendations
        correlation = pattern_analysis.get('content_correlation', {}).get('correlation_coefficient', 0)
        if correlation > 0.5:
            recommendations.append("📝 Longer messages tend to take more time. Consider breaking down complex requests")
        
        # Consistency recommendations
        std_dev = time_analysis.get('std_dev', 0)
        mean_time = time_analysis.get('mean', 1)
        if std_dev / mean_time > 0.5:  # High variability
            recommendations.append("📊 Response times vary significantly. Try to maintain consistent query complexity")
        
        return recommendations

# Enhanced session initialization with advanced performance monitoring
def init_session():
    """Initialize session with user-specific isolation and advanced performance monitoring."""
    current_user = st.session_state.get('username')
    
    if not current_user:
        return
    
    # Create user-specific keys
    user_key_prefix = f"user_{current_user}_"
    
    defaults = {
        f"{user_key_prefix}params": {},
        f"{user_key_prefix}current_chat_id": None,
        f"{user_key_prefix}current_chat_index": 0,
        f"{user_key_prefix}history_chats": get_user_history(current_user),
        f"{user_key_prefix}messages": [],
        f"{user_key_prefix}conversation_memory": [],
        f"{user_key_prefix}performance_monitor": PerformanceMonitor(),
        f"{user_key_prefix}chat_analyzer": ChatPerformanceAnalyzer(),
        "client": None,
        "agent": None,
        "tools": [],
        "tool_executions": [],
        "servers": SERVER_CONFIG['mcpServers'],
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    # Also set global keys pointing to user-specific data for backward compatibility
    st.session_state["params"] = st.session_state[f"{user_key_prefix}params"]
    st.session_state["current_chat_id"] = st.session_state[f"{user_key_prefix}current_chat_id"]
    st.session_state["current_chat_index"] = st.session_state[f"{user_key_prefix}current_chat_index"]
    st.session_state["history_chats"] = st.session_state[f"{user_key_prefix}history_chats"]
    st.session_state["messages"] = st.session_state[f"{user_key_prefix}messages"]
    st.session_state["conversation_memory"] = st.session_state[f"{user_key_prefix}conversation_memory"]

def get_user_history(username: str) -> List[Dict]:
    """Get chat history for a specific user with enhanced performance tracking."""
    user_key = f"user_{username}_history_chats"
    
    if user_key in st.session_state and st.session_state[user_key]:
        return st.session_state[user_key]
    else:
        chat_id = str(uuid.uuid4())
        new_chat = {
            'chat_id': chat_id,
            'chat_name': 'New chat',
            'messages': [],
            'created_by': username,
            'created_at': datetime.now().isoformat(),
            'performance_stats': {
                'total_processing_time': 0,
                'message_count': 0,
                'average_processing_time': 0,
                'tool_executions': 0,
                'success_rate': 100.0,
                'performance_grade': 'N/A'
            },
            'analytics': {
                'session_start': time.time(),
                'last_activity': time.time(),
                'user_efficiency_score': 0,
                'query_complexity_score': 0
            }
        }
        
        # Update user-specific session state
        st.session_state[f"user_{username}_current_chat_index"] = 0
        st.session_state[f"user_{username}_current_chat_id"] = chat_id
        st.session_state[user_key] = [new_chat]
        
        return [new_chat]

def switch_user_context(username: str):
    """Switch to a specific user's context and clear previous user data."""
    if not username:
        return
    
    # Clear any existing global references to prevent data leakage
    keys_to_clear = ["params", "current_chat_id", "current_chat_index", 
                     "history_chats", "messages", "conversation_memory"]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Initialize session for the new user
    init_session()

def get_current_chat(chat_id: str, username: str = None) -> List[Dict]:
    """Get messages for the current chat for a specific user."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return []
    
    user_history_key = f"user_{username}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    for chat in user_chats:
        if chat['chat_id'] == chat_id and chat.get('created_by') == username:
            return chat['messages']
    return []

def _append_message_to_session(msg: dict) -> None:
    """Append message to the current user's chat session with comprehensive performance tracking."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    chat_id = st.session_state.get("current_chat_id")
    if not chat_id:
        return
    
    # Get user-specific keys
    user_messages_key = f"user_{current_user}_messages"
    user_history_key = f"user_{current_user}_history_chats"
    user_perf_key = f"user_{current_user}_performance_monitor"
    
    # Avoid duplicating messages
    user_messages = st.session_state.get(user_messages_key, [])
    if user_messages and len(user_messages) > 0:
        last_message = user_messages[-1]
        # Check if this is a duplicate message
        if (last_message.get("role") == msg.get("role") and 
            last_message.get("content") == msg.get("content") and
            last_message.get("tool") == msg.get("tool")):
            return  # Don't add duplicate
    
    # Add timestamp and user info to message
    msg['timestamp'] = datetime.now().isoformat()
    msg['user'] = current_user
    msg['message_id'] = str(uuid.uuid4())  # Unique message ID
    
    # Handle tool execution messages specially
    if msg.get("role") == "tool":
        msg['message_type'] = 'tool_execution'
        # Ensure tool messages have required fields
        if 'tool_name' not in msg:
            msg['tool_name'] = msg.get('tool', 'Unknown Tool')
        
        # Record tool execution time if available
        if 'execution_time' in msg:
            performance_monitor = st.session_state.get(user_perf_key)
            if performance_monitor:
                performance_monitor.record_tool_execution(
                    msg['tool_name'], 
                    msg['execution_time'],
                    success=not msg.get('is_error', False),
                    error_msg=msg.get('error_message')
                )
    
    # Record processing time for performance monitoring
    if msg.get("role") == "assistant" and msg.get('processing_time'):
        performance_monitor = st.session_state.get(user_perf_key)
        if performance_monitor:
            message_length = len(msg.get('content', ''))
            token_count = msg.get('token_count')  # If available from AI service
            tool_used = msg.get('tool_name') if msg.get('tool_name') else None
            
            performance_monitor.record_processing_time(
                msg['processing_time'], 
                message_length,
                token_count,
                error_occurred=msg.get('is_error', False),
                tool_used=tool_used
            )
            
            # Record error if this is an error message
            if msg.get('is_error'):
                performance_monitor.record_error(
                    'processing_error',
                    msg.get('error_message', 'Unknown processing error'),
                    {
                        'message_length': message_length,
                        'processing_time': msg['processing_time']
                    }
                )
    
    # Update user-specific messages
    user_messages.append(msg)
    st.session_state[user_messages_key] = user_messages
    st.session_state["messages"] = user_messages  # Update global reference
    
    # Update the chat in user's history with comprehensive performance stats
    user_chats = st.session_state.get(user_history_key, [])
    for chat in user_chats:
        if chat["chat_id"] == chat_id and chat.get('created_by') == current_user:
            chat["messages"] = user_messages
            
            # Calculate comprehensive performance statistics
            processing_times = [m.get('processing_time') for m in user_messages if m.get('processing_time')]
            tool_messages = [m for m in user_messages if m.get('role') == 'tool']
            error_messages = [m for m in user_messages if m.get('is_error')]
            assistant_messages = [m for m in user_messages if m.get('role') == 'assistant']
            
            # Update chat performance statistics
            if processing_times:
                avg_processing_time = statistics.mean(processing_times)
                total_processing_time = sum(processing_times)
                success_rate = ((len(assistant_messages) - len(error_messages)) / max(len(assistant_messages), 1)) * 100
                
                # Calculate performance grade for this chat
                if avg_processing_time < 2 and success_rate >= 90:
                    grade = 'A'
                elif avg_processing_time < 3 and success_rate >= 80:
                    grade = 'B'
                elif avg_processing_time < 5 and success_rate >= 70:
                    grade = 'C'
                else:
                    grade = 'D'
            else:
                avg_processing_time = 0
                total_processing_time = 0
                success_rate = 100.0
                grade = 'N/A'
            
            chat['performance_stats'] = {
                'total_processing_time': total_processing_time,
                'message_count': len(user_messages),
                'average_processing_time': avg_processing_time,
                'tool_executions': len(tool_messages),
                'success_rate': success_rate,
                'error_count': len(error_messages),
                'performance_grade': grade,
                'last_updated': datetime.now().isoformat()
            }
            
            # Update analytics
            chat['analytics']['last_activity'] = time.time()
            chat['analytics']['user_efficiency_score'] = calculate_user_efficiency_score(user_messages)
            chat['analytics']['query_complexity_score'] = calculate_query_complexity_score(user_messages)
            
            # Only rename chat based on user messages, not tool messages
            if (chat["chat_name"] == "New chat" and 
                msg["role"] == "user" and 
                "content" in msg):                 
                chat["chat_name"] = " ".join(msg["content"].split()[:5]) or "Empty"
            chat["last_updated"] = datetime.now().isoformat()
            break
    
    st.session_state[user_history_key] = user_chats
    st.session_state["history_chats"] = user_chats  # Update global reference

def calculate_user_efficiency_score(messages: List[Dict]) -> float:
    """Calculate user efficiency score based on message patterns."""
    if not messages:
        return 0.0
    
    user_messages = [m for m in messages if m.get('role') == 'user']
    assistant_messages = [m for m in messages if m.get('role') == 'assistant']
    
    if not user_messages:
        return 0.0
    
    # Factors for efficiency score
    # 1. Message length appropriateness (not too short, not too long)
    avg_message_length = statistics.mean([len(m.get('content', '')) for m in user_messages])
    length_score = min(100, max(0, 100 - abs(avg_message_length - 100) / 2))  # Optimal around 100 chars
    
    # 2. Error rate (fewer errors = higher efficiency)
    error_messages = [m for m in assistant_messages if m.get('is_error')]
    error_rate = (len(error_messages) / max(len(assistant_messages), 1)) * 100
    error_score = max(0, 100 - error_rate * 2)  # Penalty for errors
    
    # 3. Response time correlation (consistent queries = higher efficiency)
    processing_times = [m.get('processing_time') for m in assistant_messages if m.get('processing_time')]
    if len(processing_times) > 1:
        time_consistency = 100 - min(100, statistics.stdev(processing_times) * 20)
    else:
        time_consistency = 100
    
    # Combined efficiency score
    efficiency_score = (length_score * 0.3) + (error_score * 0.5) + (time_consistency * 0.2)
    return min(100, max(0, efficiency_score))

def calculate_query_complexity_score(messages: List[Dict]) -> float:
    """Calculate average query complexity based on message content."""
    user_messages = [m for m in messages if m.get('role') == 'user']
    
    if not user_messages:
        return 0.0
    
    complexity_scores = []
    
    for message in user_messages:
        content = message.get('content', '').lower()
        complexity = 0
        
        # Keywords that indicate complexity
        complex_keywords = ['join', 'group by', 'order by', 'having', 'subquery', 'union', 'aggregate']
        moderate_keywords = ['where', 'select', 'from', 'update', 'insert', 'delete']
        
        complexity += sum(5 for keyword in complex_keywords if keyword in content)
        complexity += sum(2 for keyword in moderate_keywords if keyword in content)
        
        # Length factor
        if len(content) > 200:
            complexity += 10
        elif len(content) > 100:
            complexity += 5
        
        complexity_scores.append(min(100, complexity))
    
    return statistics.mean(complexity_scores)

def append_tool_execution_message(tool_name: str, tool_input: Dict, tool_output: str, 
                                execution_time: float = None, success: bool = True,
                                error_message: str = None) -> None:
    """Append a comprehensive tool execution message to the chat history."""
    tool_message = {
        "role": "tool",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "content": tool_output,
        "timestamp": datetime.now().isoformat(),
        "message_type": "tool_execution",
        "execution_time": execution_time,
        "success": success,
        "error_message": error_message,
        "is_error": not success
    }
    _append_message_to_session(tool_message)

def create_chat() -> Dict:
    """Create a new chat session for the current user with enhanced initialization."""
    current_user = st.session_state.get('username')
    if not current_user:
        return {}
    
    chat_id = str(uuid.uuid4())
    new_chat = {
        'chat_id': chat_id,
        'chat_name': 'New chat',
        'messages': [],
        'created_by': current_user,
        'created_at': datetime.now().isoformat(),
        'performance_stats': {
            'total_processing_time': 0,
            'message_count': 0,
            'average_processing_time': 0,
            'tool_executions': 0,
            'success_rate': 100.0,
            'performance_grade': 'N/A'
        },
        'analytics': {
            'session_start': time.time(),
            'last_activity': time.time(),
            'user_efficiency_score': 0,
            'query_complexity_score': 0,
            'expected_performance': 'unknown'  # Will be updated based on user patterns
        }
    }
    
    # Get user-specific keys
    user_history_key = f"user_{current_user}_history_chats"
    user_messages_key = f"user_{current_user}_messages"
    user_memory_key = f"user_{current_user}_conversation_memory"
    
    # Update user-specific session state
    user_chats = st.session_state.get(user_history_key, [])
    user_chats.append(new_chat)
    
    st.session_state[user_history_key] = user_chats
    st.session_state[f"user_{current_user}_current_chat_index"] = 0
    st.session_state[f"user_{current_user}_current_chat_id"] = chat_id
    st.session_state[user_messages_key] = []
    st.session_state[user_memory_key] = []
    
    # Update global references
    st.session_state["history_chats"] = user_chats
    st.session_state["current_chat_id"] = chat_id
    st.session_state["current_chat_index"] = 0
    st.session_state["messages"] = []
    st.session_state["conversation_memory"] = []
    
    return new_chat

def switch_chat(chat_id: str):
    """Switch to a different chat for the current user."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    current_chat_id = st.session_state.get("current_chat_id")
    if chat_id == current_chat_id:
        return  # Already on this chat
    
    # Get user-specific keys
    user_history_key = f"user_{current_user}_history_chats"
    user_messages_key = f"user_{current_user}_messages"
    user_memory_key = f"user_{current_user}_conversation_memory"
    
    # Get chat messages for this user only
    chat_messages = get_current_chat(chat_id, current_user)
    
    # Verify the chat belongs to the current user
    user_chats = st.session_state.get(user_history_key, [])
    target_chat = None
    for i, chat in enumerate(user_chats):
        if chat["chat_id"] == chat_id and chat.get('created_by') == current_user:
            target_chat = chat
            st.session_state[f"user_{current_user}_current_chat_index"] = i
            break
    
    if not target_chat:
        return  # Chat not found or doesn't belong to user
    
    # Update user-specific session state
    st.session_state[f"user_{current_user}_current_chat_id"] = chat_id
    st.session_state[user_messages_key] = chat_messages
    st.session_state[user_memory_key] = []  # Reset conversation memory for new chat
    
    # Update global references
    st.session_state["current_chat_id"] = chat_id
    st.session_state["messages"] = chat_messages
    st.session_state["conversation_memory"] = []

def delete_chat(chat_id: str):
    """Delete a chat from the current user's history."""
    current_user = st.session_state.get('username')
    if not current_user or not chat_id:
        return

    # Get user-specific keys
    user_history_key = f"user_{current_user}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    # Remove chat only if it belongs to the current user
    updated_chats = [
        chat for chat in user_chats
        if not (chat["chat_id"] == chat_id and chat.get('created_by') == current_user)
    ]
    
    if len(updated_chats) == len(user_chats):
        return  # Chat not found or doesn't belong to user
    
    st.session_state[user_history_key] = updated_chats
    st.session_state["history_chats"] = updated_chats  # Update global reference

    # Handle current chat deletion
    current_chat_id = st.session_state.get("current_chat_id")
    if current_chat_id == chat_id:
        if updated_chats:
            # Switch to the first available chat
            first_chat = updated_chats[0]
            st.session_state[f"user_{current_user}_current_chat_id"] = first_chat["chat_id"]
            st.session_state[f"user_{current_user}_current_chat_index"] = 0
            st.session_state[f"user_{current_user}_messages"] = first_chat["messages"]
            
            # Update global references
            st.session_state["current_chat_id"] = first_chat["chat_id"]
            st.session_state["current_chat_index"] = 0
            st.session_state["messages"] = first_chat["messages"]
        else:
            # No chats left, create a new one
            create_chat()
        
        # Clear conversation memory when switching/deleting chats
        st.session_state[f"user_{current_user}_conversation_memory"] = []
        st.session_state["conversation_memory"] = []

def get_conversation_summary(max_messages: int = 10) -> str:
    """Get a summary of recent conversation for current user."""
    current_user = st.session_state.get('username')
    if not current_user:
        return "Please log in to view conversation."
    
    user_messages = st.session_state.get(f"user_{current_user}_messages", [])
    if not user_messages:
        return "This is the start of a new conversation."
    
    recent_messages = user_messages[-max_messages:]
    summary_parts = []
    
    for msg in recent_messages:
        if msg["role"] == "user":
            summary_parts.append(f"User: {msg['content'][:100]}...")
        elif msg["role"] == "assistant" and "content" in msg and msg["content"]:
            summary_parts.append(f"Assistant: {msg['content'][:100]}...")
        elif msg["role"] == "tool":
            tool_name = msg.get('tool_name', 'Unknown Tool')
            summary_parts.append(f"Tool ({tool_name}): {msg['content'][:50]}...")
    
    return "\n".join(summary_parts)

def get_clean_conversation_memory() -> List:
    """Get conversation memory with only user/assistant content messages for LLM compatibility."""
    current_user = st.session_state.get('username')
    if not current_user:
        return []
    
    conversation_messages = []
    
    current_chat_id = st.session_state.get('current_chat_id')
    if current_chat_id:
        messages = get_current_chat(current_chat_id, current_user)
        
        for msg in messages:
            # Only include messages from the current user's session
            if msg.get('user') == current_user:
                if msg["role"] == "user" and "content" in msg:
                    conversation_messages.append(HumanMessage(content=msg["content"]))
                elif (msg["role"] == "assistant" and 
                      "content" in msg and 
                      msg["content"] and 
                      msg.get("message_type") != "tool_execution"):  # Exclude tool execution messages from LLM memory
                    conversation_messages.append(AIMessage(content=msg["content"]))
                # Note: Tool messages are not included in LLM conversation memory
                # but are stored separately in chat history for display purposes
    
    return conversation_messages

def clear_user_session_data(username: str):
    """Clear all session data for a specific user (useful for logout)."""
    if not username:
        return
    
    user_keys_to_clear = [
        f"user_{username}_params",
        f"user_{username}_current_chat_id",
        f"user_{username}_current_chat_index",
        f"user_{username}_history_chats",
        f"user_{username}_messages",
        f"user_{username}_conversation_memory",
        f"user_{username}_performance_monitor",
        f"user_{username}_chat_analyzer"
    ]
    
    for key in user_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Enhanced ChatService with comprehensive performance tracking
class ChatService:
    """Enhanced ChatService with comprehensive performance monitoring and analytics."""
    
    def __init__(self):
        """Initialize the enhanced chat service."""
        self.agent = None
        self.tools = []
        self.processing_start_times = {}  # Track processing start times
        self.request_counter = 0
        
    def process_message(self, user_input: str) -> str:
        """
        Process a user message and return the AI response with basic timing.
        
        Args:
            user_input: The user's input message
            
        Returns:
            The AI agent's response
        """
        try:
            # Check authentication
            current_user = st.session_state.get('username')
            if not current_user:
                return "❌ Please log in to use the chat service."
            
            # Get the agent from session state
            if not st.session_state.get("agent"):
                return "❌ No MCP agent available. Please connect to MCP servers first."
            
            # Get conversation history for current user (excluding tool messages)
            conversation_messages = get_clean_conversation_memory()
            
            # Add the current user message
            conversation_messages.append(HumanMessage(content=user_input))
            
            # Run the agent with conversation context
            response = run_async(self._run_agent_async(conversation_messages))
            
            # Handle tool executions in the response if any
            self._process_tool_calls_in_response(response)
            
            # Extract the response content
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, dict) and 'messages' in response:
                # Extract the last message content
                messages = response['messages']
                if messages and hasattr(messages[-1], 'content'):
                    return messages[-1].content
                elif messages and isinstance(messages[-1], dict):
                    return messages[-1].get('content', str(messages[-1]))
            
            return str(response)
            
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            logging.error(f"ChatService error: {str(e)}")
            return error_message
    
    def process_message_with_comprehensive_timing(self, user_input: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Process a user message with comprehensive timing and performance tracking.
        
        Args:
            user_input: The user's input message
            
        Returns:
            Tuple of (response, processing_time, performance_details)
        """
        start_time = time.time()
        current_user = st.session_state.get('username')
        request_id = f"{current_user}_{self.request_counter}_{int(start_time)}"
        self.request_counter += 1
        
        if not current_user:
            return "❌ Please log in to use the chat service.", 0, {'error': 'no_auth'}
        
        performance_details = {
            'request_id': request_id,
            'start_time': start_time,
            'user_input_length': len(user_input),
            'estimated_input_tokens': len(user_input) // 4,
            'tool_executions': [],
            'errors': [],
            'phases': {},
            'memory_usage': {},
            'agent_details': {}
        }
        
        try:
            # Phase 1: Authentication and setup
            phase_start = time.time()
            
            # Check agent availability
            if not st.session_state.get("agent"):
                processing_time = time.time() - start_time
                performance_details['phases']['total'] = processing_time
                performance_details['errors'].append('No MCP agent available')
                return "❌ No MCP agent available. Please connect to MCP servers first.", processing_time, performance_details
            
            performance_details['phases']['setup'] = time.time() - phase_start
            
            # Phase 2: Conversation preparation
            phase_start = time.time()
            conversation_messages = get_clean_conversation_memory()
            conversation_messages.append(HumanMessage(content=user_input))
            
            performance_details['phases']['conversation_prep'] = time.time() - phase_start
            performance_details['conversation_length'] = len(conversation_messages)
            
            # Phase 3: Agent processing
            phase_start = time.time()
            response = run_async(self._run_agent_async(conversation_messages))
            agent_processing_time = time.time() - phase_start
            performance_details['phases']['agent_processing'] = agent_processing_time
            
            # Phase 4: Tool processing
            phase_start = time.time()
            tool_calls = self._process_tool_calls_in_response(response)
            tool_processing_time = time.time() - phase_start
            performance_details['phases']['tool_processing'] = tool_processing_time
            performance_details['tool_executions'] = tool_calls
            
            # Phase 5: Response extraction
            phase_start = time.time()
            response_content = self._extract_response_content(response)
            extraction_time = time.time() - phase_start
            performance_details['phases']['response_extraction'] = extraction_time
            
            # Final metrics
            total_processing_time = time.time() - start_time
            performance_details['phases']['total'] = total_processing_time
            performance_details['response_length'] = len(response_content)
            performance_details['estimated_output_tokens'] = len(response_content) // 4
            performance_details['end_time'] = time.time()
            
            # Calculate efficiency metrics
            performance_details['efficiency'] = {
                'tokens_per_second': (performance_details['estimated_input_tokens'] + 
                                    performance_details['estimated_output_tokens']) / max(total_processing_time, 0.1),
                'chars_per_second': (len(user_input) + len(response_content)) / max(total_processing_time, 0.1),
                'processing_overhead': (total_processing_time - agent_processing_time) / max(total_processing_time, 0.1)
            }
            
            return response_content, total_processing_time, performance_details
            
        except Exception as e:
            # Record error details
            error_time = time.time() - start_time
            performance_details['phases']['total'] = error_time
            performance_details['errors'].append({
                'error': str(e),
                'error_time': error_time,
                'error_type': type(e).__name__,
                'traceback': str(e)
            })
            
            # Record error in performance monitor
            user_perf_key = f"user_{current_user}_performance_monitor"
            performance_monitor = st.session_state.get(user_perf_key)
            if performance_monitor:
                performance_monitor.record_error('processing_error', str(e), performance_details)
            
            error_message = f"Error processing message: {str(e)}"
            return error_message, error_time, performance_details
    
    async def _run_agent_async(self, messages: List) -> Any:
        """
        Run the agent asynchronously with the given messages including system prompt.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Agent response
        """
        agent = st.session_state["agent"]
        
        # Prepend system prompt if available
        system_prompt = st.session_state.get("system_prompt")
        if system_prompt:
            # Add system message at the beginning
            system_message = SystemMessage(content=system_prompt)
            messages = [system_message] + messages
        
        # Invoke the agent with the messages
        result = await agent.ainvoke({"messages": messages})
        
        return result
    
    def _process_tool_calls_in_response(self, response: Any) -> List[Dict[str, Any]]:
        """Process any tool calls that occurred during the agent response."""
        tool_calls = []
        
        try:
            # Check if the response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_execution = {
                        'tool_name': tool_call.get('name', 'Unknown Tool'),
                        'tool_input': tool_call.get('args', {}),
                        'tool_output': str(tool_call.get('output', 'No output')),
                        'execution_time': tool_call.get('execution_time', 0),
                        'success': tool_call.get('success', True)
                    }
                    tool_calls.append(tool_execution)
                    
                    # Log the tool execution with comprehensive details
                    append_tool_execution_message(
                        tool_execution['tool_name'], 
                        tool_execution['tool_input'], 
                        tool_execution['tool_output'],
                        execution_time=tool_execution['execution_time'],
                        success=tool_execution['success']
                    )
            
            # Also check if response is a dict with tool execution info
            elif isinstance(response, dict):
                if 'tool_calls' in response:
                    for tool_call in response['tool_calls']:
                        tool_execution = {
                            'tool_name': tool_call.get('name', 'Unknown Tool'),
                            'tool_input': tool_call.get('args', {}),
                            'tool_output': str(tool_call.get('output', 'No output')),
                            'execution_time': tool_call.get('execution_time', 0),
                            'success': tool_call.get('success', True)
                        }
                        tool_calls.append(tool_execution)
                        
                        # Log the tool execution
                        append_tool_execution_message(
                            tool_execution['tool_name'], 
                            tool_execution['tool_input'], 
                            tool_execution['tool_output'],
                            execution_time=tool_execution['execution_time'],
                            success=tool_execution['success']
                        )
                
                # Check for messages with tool content
                elif 'messages' in response:
                    for msg in response['messages']:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_execution = {
                                    'tool_name': tool_call.get('name', 'Unknown Tool'),
                                    'tool_input': tool_call.get('args', {}),
                                    'tool_output': str(tool_call.get('output', 'No output')),
                                    'execution_time': tool_call.get('execution_time', 0),
                                    'success': tool_call.get('success', True)
                                }
                                tool_calls.append(tool_execution)
                                
                                # Log the tool execution
                                append_tool_execution_message(
                                    tool_execution['tool_name'], 
                                    tool_execution['tool_input'], 
                                    tool_execution['tool_output'],
                                    execution_time=tool_execution['execution_time'],
                                    success=tool_execution['success']
                                )
        
        except Exception as e:
            # Don't fail the main response processing if tool logging fails
            logging.error(f"Error processing tool calls: {str(e)}")
            tool_calls.append({
                'tool_name': 'Error',
                'tool_input': {},
                'tool_output': f'Error processing tool calls: {str(e)}',
                'execution_time': 0,
                'success': False
            })
        
        return tool_calls
    
    def _extract_response_content(self, response: Any) -> str:
        """Extract response content with comprehensive error handling."""
        try:
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, dict) and 'messages' in response:
                messages = response['messages']
                if messages and hasattr(messages[-1], 'content'):
                    return messages[-1].content
                elif messages and isinstance(messages[-1], dict):
                    return messages[-1].get('content', str(messages[-1]))
            return str(response)
        except Exception as e:
            logging.error(f"Error extracting response content: {str(e)}")
            return f"Error extracting response: {str(e)}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = st.session_state.get("tools", [])
        return [tool.name for tool in tools]
    
    def is_connected(self) -> bool:
        """Check if the chat service is connected to MCP servers."""
        return st.session_state.get("agent") is not None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status with performance metrics."""
        current_user = st.session_state.get('username')
        
        # Basic connection info
        status = {
            "connected": self.is_connected(),
            "agent_available": st.session_state.get("agent") is not None,
            "tools_count": len(st.session_state.get("tools", [])),
            "servers_count": len(st.session_state.get("servers", {})),
            "available_tools": self.get_available_tools(),
            "current_user": current_user
        }
        
        # Add performance metrics if user is logged in
        if current_user:
            user_perf_key = f"user_{current_user}_performance_monitor"
            performance_monitor = st.session_state.get(user_perf_key)
            
            if performance_monitor:
                perf_summary = performance_monitor.get_performance_summary()
                status["performance"] = {
                    "session_active": perf_summary.get('status') == 'active',
                    "total_messages": perf_summary.get('total_messages', 0),
                    "average_response_time": perf_summary.get('average_processing_time', 0),
                    "performance_grade": perf_summary.get('performance_grade', 'N/A'),
                    "success_rate": perf_summary.get('success_rate', 100),
                    "tool_executions": perf_summary.get('total_tool_executions', 0)
                }
        
        return status
    
    def get_processing_analytics(self) -> Dict[str, Any]:
        """Get comprehensive processing analytics for the current session."""
        current_user = st.session_state.get('username')
        if not current_user:
            return {'status': 'no_user'}
        
        # Get performance stats
        perf_stats = get_user_performance_stats(current_user)
        perf_trends = get_user_performance_trends(current_user)
        chat_comparison = get_chat_performance_comparison(current_user)
        
        # Get tool performance analysis
        user_perf_key = f"user_{current_user}_performance_monitor"
        performance_monitor = st.session_state.get(user_perf_key)
        tool_analysis = {}
        
        if performance_monitor:
            tool_analysis = performance_monitor.get_tool_performance_analysis()
        
        # Get chat analysis
        user_analyzer_key = f"user_{current_user}_chat_analyzer"
        chat_analyzer = st.session_state.get(user_analyzer_key)
        chat_analysis = {}
        
        if chat_analyzer:
            chat_analysis = chat_analyzer.analyze_chat_performance(current_user)
        
        return {
            'performance_stats': perf_stats,
            'performance_trends': perf_trends,
            'chat_comparison': chat_comparison,
            'tool_analysis': tool_analysis,
            'chat_analysis': chat_analysis,
            'generated_at': datetime.now().isoformat(),
            'session_summary': self._generate_session_summary(perf_stats, tool_analysis)
        }
    
    def _generate_session_summary(self, perf_stats: Dict, tool_analysis: Dict) -> Dict[str, Any]:
        """Generate a comprehensive session summary."""
        if perf_stats.get('status') != 'active':
            return {'status': 'no_data'}
        
        # Calculate session insights
        session_duration = perf_stats.get('session_duration_minutes', 0)
        total_messages = perf_stats.get('total_messages', 0)
        avg_response_time = perf_stats.get('average_processing_time', 0)
        
        # Determine session characteristics
        if session_duration < 5:
            session_type = 'Quick Session'
        elif session_duration < 30:
            session_type = 'Standard Session'
        elif session_duration < 60:
            session_type = 'Extended Session'
        else:
            session_type = 'Marathon Session'
        
        # Performance classification
        if avg_response_time < 2:
            performance_class = 'High Performance'
        elif avg_response_time < 5:
            performance_class = 'Good Performance'
        elif avg_response_time < 10:
            performance_class = 'Moderate Performance'
        else:
            performance_class = 'Needs Optimization'
        
        # Usage pattern analysis
        messages_per_minute = perf_stats.get('messages_per_minute', 0)
        if messages_per_minute > 3:
            usage_pattern = 'High Intensity'
        elif messages_per_minute > 1:
            usage_pattern = 'Moderate Usage'
        else:
            usage_pattern = 'Light Usage'
        
        # Tool usage analysis
        tool_stats = tool_analysis.get('summary', {})
        tool_usage_intensity = 'Low'
        if tool_stats.get('total_executions', 0) > total_messages * 0.5:
            tool_usage_intensity = 'High'
        elif tool_stats.get('total_executions', 0) > total_messages * 0.2:
            tool_usage_intensity = 'Medium'
        
        return {
            'status': 'active',
            'session_type': session_type,
            'performance_class': performance_class,
            'usage_pattern': usage_pattern,
            'tool_usage_intensity': tool_usage_intensity,
            'session_insights': {
                'most_productive_hour': self._find_most_productive_hour(perf_stats),
                'efficiency_trend': self._calculate_efficiency_trend(perf_stats),
                'consistency_score': self._calculate_consistency_score(perf_stats)
            }
        }
    
    def _find_most_productive_hour(self, perf_stats: Dict) -> Optional[int]:
        """Find the hour with best performance."""
        hourly_perf = perf_stats.get('hourly_performance', {})
        if not hourly_perf:
            return None
        
        best_hour = None
        best_score = float('inf')
        
        for hour, stats in hourly_perf.items():
            # Score based on average response time and message count
            avg_time = stats.get('average', 10)
            count = stats.get('count', 1)
            score = avg_time / (count ** 0.5)  # Lower is better
            
            if score < best_score:
                best_score = score
                best_hour = int(hour)
        
        return best_hour
    
    def _calculate_efficiency_trend(self, perf_stats: Dict) -> str:
        """Calculate overall efficiency trend."""
        trends = perf_stats.get('trends', {})
        
        if 'long_term' in trends:
            direction = trends['long_term'].get('direction', 'stable')
            magnitude = trends['long_term'].get('magnitude_percent', 0)
            
            if direction == 'improving' and magnitude > 5:
                return 'Significantly Improving'
            elif direction == 'improving':
                return 'Improving'
            elif direction == 'declining' and magnitude > 5:
                return 'Declining'
            elif direction == 'declining':
                return 'Slightly Declining'
            else:
                return 'Stable'
        
        return 'Unknown'
    
    def _calculate_consistency_score(self, perf_stats: Dict) -> float:
        """Calculate performance consistency score (0-100)."""
        std_dev = perf_stats.get('std_dev_processing_time', 0)
        avg_time = perf_stats.get('average_processing_time', 1)
        
        # Consistency score based on coefficient of variation
        cv = std_dev / avg_time if avg_time > 0 else 0
        consistency_score = max(0, 100 - (cv * 100))
        
        return min(100, consistency_score)

# Enhanced utility functions for performance analytics
def get_user_performance_stats(username: str = None) -> Dict[str, Any]:
    """Get comprehensive performance statistics for a user."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return {"status": "no_user"}
    
    user_perf_key = f"user_{username}_performance_monitor"
    performance_monitor = st.session_state.get(user_perf_key)
    
    if not performance_monitor:
        return {"status": "no_monitor"}
    
    return performance_monitor.get_performance_summary()

def get_user_performance_trends(username: str = None, window_size: int = 5) -> Dict[str, Any]:
    """Get performance trends for a user."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return {"status": "no_user"}
    
    user_perf_key = f"user_{username}_performance_monitor"
    performance_monitor = st.session_state.get(user_perf_key)
    
    if not performance_monitor:
        return {"status": "no_monitor"}
    
    return performance_monitor.get_performance_trends(window_size)

def get_chat_performance_comparison(username: str = None) -> Dict[str, Any]:
    """Compare performance across different chats for a user."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return {"status": "no_user"}
    
    user_history_key = f"user_{username}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    chat_performances = []
    
    for chat in user_chats:
        if chat.get('created_by') == username and chat.get('performance_stats'):
            stats = chat['performance_stats']
            analytics = chat.get('analytics', {})
            
            chat_performances.append({
                'chat_id': chat['chat_id'],
                'chat_name': chat['chat_name'],
                'message_count': stats.get('message_count', 0),
                'average_processing_time': stats.get('average_processing_time', 0),
                'total_processing_time': stats.get('total_processing_time', 0),
                'tool_executions': stats.get('tool_executions', 0),
                'success_rate': stats.get('success_rate', 100),
                'performance_grade': stats.get('performance_grade', 'N/A'),
                'user_efficiency_score': analytics.get('user_efficiency_score', 0),
                'query_complexity_score': analytics.get('query_complexity_score', 0),
                'created_at': chat.get('created_at'),
                'last_updated': stats.get('last_updated'),
                'session_duration': analytics.get('last_activity', 0) - analytics.get('session_start', 0) if analytics.get('session_start') else 0
            })
    
    if not chat_performances:
        return {"status": "no_data"}
    
    # Calculate comprehensive statistics
    total_messages = sum(chat['message_count'] for chat in chat_performances)
    total_time = sum(chat['total_processing_time'] for chat in chat_performances)
    total_session_time = sum(chat['session_duration'] for chat in chat_performances)
    
    # Find best and worst performing chats
    active_chats = [chat for chat in chat_performances if chat['message_count'] > 0]
    
    if active_chats:
        best_response_time_chat = min(active_chats, key=lambda x: x['average_processing_time'])
        worst_response_time_chat = max(active_chats, key=lambda x: x['average_processing_time'])
        best_efficiency_chat = max(active_chats, key=lambda x: x['user_efficiency_score'])
        most_complex_chat = max(active_chats, key=lambda x: x['query_complexity_score'])
    else:
        best_response_time_chat = worst_response_time_chat = best_efficiency_chat = most_complex_chat = None
    
    return {
        "status": "success",
        "total_chats": len(chat_performances),
        "active_chats": len(active_chats),
        "total_messages": total_messages,
        "total_processing_time": total_time,
        "total_session_time": total_session_time,
        "overall_average_response_time": total_time / total_messages if total_messages > 0 else 0,
        "average_session_duration": total_session_time / len(chat_performances) if chat_performances else 0,
        "best_response_time_chat": best_response_time_chat,
        "worst_response_time_chat": worst_response_time_chat,
        "best_efficiency_chat": best_efficiency_chat,
        "most_complex_chat": most_complex_chat,
        "chat_details": sorted(chat_performances, key=lambda x: x['average_processing_time']),
        "performance_distribution": calculate_performance_distribution(chat_performances)
    }

def calculate_performance_distribution(chat_performances: List[Dict]) -> Dict[str, Any]:
    """Calculate performance distribution across chats."""
    if not chat_performances:
        return {}
    
    response_times = [chat['average_processing_time'] for chat in chat_performances if chat['average_processing_time'] > 0]
    efficiency_scores = [chat['user_efficiency_score'] for chat in chat_performances]
    complexity_scores = [chat['query_complexity_score'] for chat in chat_performances]
    
    distribution = {}
    
    if response_times:
        distribution['response_time'] = {
            'fast_chats': len([t for t in response_times if t < 2]),
            'medium_chats': len([t for t in response_times if 2 <= t < 5]),
            'slow_chats': len([t for t in response_times if t >= 5]),
            'average': statistics.mean(response_times),
            'median': statistics.median(response_times),
            'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0
        }
    
    if efficiency_scores:
        distribution['efficiency'] = {
            'high_efficiency': len([s for s in efficiency_scores if s > 80]),
            'medium_efficiency': len([s for s in efficiency_scores if 50 < s <= 80]),
            'low_efficiency': len([s for s in efficiency_scores if s <= 50]),
            'average': statistics.mean(efficiency_scores)
        }
    
    if complexity_scores:
        distribution['complexity'] = {
            'simple_queries': len([s for s in complexity_scores if s < 30]),
            'moderate_queries': len([s for s in complexity_scores if 30 <= s < 70]),
            'complex_queries': len([s for s in complexity_scores if s >= 70]),
            'average': statistics.mean(complexity_scores)
        }
    
    return distribution

def get_user_chat_stats(username: str = None) -> Dict[str, int]:
    """Get enhanced chat statistics for a user including performance metrics."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return {"total_chats": 0, "total_messages": 0, "tool_executions": 0}
    
    user_history_key = f"user_{username}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    # Filter chats to only include those created by current user
    user_owned_chats = [chat for chat in user_chats if chat.get('created_by') == username]
    
    total_chats = len(user_owned_chats)
    total_messages = 0
    tool_executions = 0
    total_processing_time = 0
    successful_messages = 0
    
    for chat in user_owned_chats:
        chat_messages = chat.get('messages', [])
        total_messages += len(chat_messages)
        
        # Count tool executions and processing times
        for msg in chat_messages:
            if msg.get('role') == 'tool' or msg.get('message_type') == 'tool_execution':
                tool_executions += 1
            
            if msg.get('processing_time'):
                total_processing_time += msg['processing_time']
            
            if msg.get('role') == 'assistant' and not msg.get('is_error'):
                successful_messages += 1
    
    return {
        "total_chats": total_chats,
        "total_messages": total_messages,
        "tool_executions": tool_executions,
        "total_processing_time": total_processing_time,
        "average_processing_time": total_processing_time / max(successful_messages, 1),
        "successful_messages": successful_messages,
        "success_rate": (successful_messages / max(total_messages, 1)) * 100,
        "user": username
    }

def get_messages_by_type(username: str = None) -> Dict[str, List]:
    """Get messages categorized by type for a user with performance data."""
    if not username:
        username = st.session_state.get('username')
    
    if not username:
        return {"user": [], "assistant": [], "tool": []}
    
    user_messages_key = f"user_{username}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    categorized = {"user": [], "assistant": [], "tool": [], "performance_summary": {}}
    
    processing_times = []
    tool_execution_times = []
    
    for msg in messages:
        role = msg.get('role', 'unknown')
        if role in categorized:
            categorized[role].append(msg)
        
        # Collect performance data
        if msg.get('processing_time'):
            processing_times.append(msg['processing_time'])
        
        if msg.get('execution_time'):
            tool_execution_times.append(msg['execution_time'])
    
    # Add performance summary
    if processing_times:
        categorized['performance_summary'] = {
            'total_responses': len(processing_times),
            'average_response_time': statistics.mean(processing_times),
            'fastest_response': min(processing_times),
            'slowest_response': max(processing_times),
            'total_processing_time': sum(processing_times)
        }
    
    if tool_execution_times:
        categorized['performance_summary']['tool_performance'] = {
            'total_tool_executions': len(tool_execution_times),
            'average_tool_time': statistics.mean(tool_execution_times),
            'total_tool_time': sum(tool_execution_times)
        }
    
    return categorized

# Performance optimization suggestions with enhanced criteria
def get_performance_suggestions(performance_stats: Dict[str, Any]) -> List[str]:
    """Generate comprehensive performance optimization suggestions based on detailed stats."""
    suggestions = []
    
    if performance_stats.get('status') != 'active':
        return ['No performance data available for analysis.']
    
    avg_time = performance_stats.get('average_processing_time', 0)
    success_rate = performance_stats.get('success_rate', 100)
    error_rate = 100 - success_rate
    efficiency_score = performance_stats.get('efficiency_score', 0)
    tool_success_rate = performance_stats.get('tool_success_rate', 100)
    
    # Response time suggestions with more detailed criteria
    if avg_time > 15:
        suggestions.append("🚨 Very slow response times detected. Critical optimizations needed:")
        suggestions.append("  • Break complex queries into multiple smaller requests")
        suggestions.append("  • Check network connectivity and server status")
        suggestions.append("  • Consider simplifying query complexity")
        suggestions.append("  • Use specific table/column names instead of broad searches")
    elif avg_time > 10:
        suggestions.append("⚠️ Slow response times. Performance improvements recommended:")
        suggestions.append("  • Optimize query structure and specificity")
        suggestions.append("  • Use schema exploration tools before complex operations")
        suggestions.append("  • Consider breaking down multi-step processes")
    elif avg_time > 5:
        suggestions.append("⚡ Moderate response times. Minor optimizations possible:")
        suggestions.append("  • Be more specific in database queries")
        suggestions.append("  • Use targeted tools instead of general queries")
    elif avg_time < 2:
        suggestions.append("✅ Excellent response times! Optimal performance achieved.")
    elif avg_time < 3:
        suggestions.append("✅ Good response times. Well-optimized queries.")
    
    # Success rate and error analysis
    if error_rate > 25:
        suggestions.append("🚨 High error rate requires immediate attention:")
        suggestions.append("  • Verify database connectivity and permissions")
        suggestions.append("  • Double-check SQL syntax and table/column names")
        suggestions.append("  • Use schema exploration tools before queries")
        suggestions.append("  • Consider simpler query structures")
    elif error_rate > 15:
        suggestions.append("⚠️ Elevated error rate detected:")
        suggestions.append("  • Review recent error messages for patterns")
        suggestions.append("  • Validate table and column names before querying")
        suggestions.append("  • Use 'list_tables' and 'describe_table' tools first")
    elif error_rate > 5:
        suggestions.append("⚠️ Some errors detected. Room for improvement:")
        suggestions.append("  • Pay attention to SQL syntax specifics")
        suggestions.append("  • Verify data types in queries")
    elif error_rate < 2:
        suggestions.append("✅ Excellent success rate! High-quality queries.")
    
    # Tool usage analysis
    tool_executions = performance_stats.get('tool_executions', 0)
    total_messages = performance_stats.get('total_messages', 0)
    tool_ratio = tool_executions / max(total_messages, 1)
    
    if tool_ratio > 0.8:
        suggestions.append("🔧 Excellent tool utilization! You're maximizing available capabilities.")
    elif tool_ratio > 0.5:
        suggestions.append("👍 Good tool usage. Consider exploring additional tools for optimization.")
    elif tool_ratio < 0.3:
        suggestions.append("💡 Low tool usage detected. Consider using more database tools:")
        suggestions.append("  • Use 'list_tables' to explore database structure")
        suggestions.append("  • Use 'describe_table' to understand table schemas")
        suggestions.append("  • Use 'get_table_sample' to see example data")
        suggestions.append("  • Leverage specialized tools for specific operations")
    
    # Tool success rate
    if tool_success_rate < 80:
        suggestions.append("🔧 Tool execution issues detected:")
        suggestions.append("  • Review tool parameter requirements")
        suggestions.append("  • Ensure proper data types in tool inputs")
        suggestions.append("  • Check tool documentation for correct usage")
    elif tool_success_rate > 95:
        suggestions.append("✅ Excellent tool success rate!")
    
    # Efficiency analysis
    if efficiency_score < 30:
        suggestions.append("📊 Low efficiency score. Comprehensive optimization needed:")
        suggestions.append("  • Focus on query simplification and specificity")
        suggestions.append("  • Improve error handling and validation")
        suggestions.append("  • Use consistent query patterns")
    elif efficiency_score < 60:
        suggestions.append("📈 Moderate efficiency. Some optimizations recommended:")
        suggestions.append("  • Work on query consistency")
        suggestions.append("  • Reduce error rates through better validation")
    elif efficiency_score > 80:
        suggestions.append("✅ High efficiency score! Excellent query patterns.")
    
    # Consistency suggestions
    std_dev = performance_stats.get('std_dev_processing_time', 0)
    if avg_time > 0 and std_dev / avg_time > 0.5:
        suggestions.append("📊 High response time variability detected:")
        suggestions.append("  • Maintain consistent query complexity")
        suggestions.append("  • Standardize your querying approach")
        suggestions.append("  • Avoid mixing simple and very complex queries")
    
    # Session-specific suggestions
    session_duration = performance_stats.get('session_duration_minutes', 0)
    messages_per_minute = performance_stats.get('messages_per_minute', 0)
    
    if session_duration > 60:
        suggestions.append("⏰ Extended session detected:")
        suggestions.append("  • Consider taking breaks to maintain query quality")
        suggestions.append("  • Review performance patterns for fatigue effects")
    
    if messages_per_minute > 4:
        suggestions.append("⚡ High message frequency:")
        suggestions.append("  • Ensure quality over quantity in queries")
        suggestions.append("  • Allow time for thoughtful query formulation")
    
    # Trend-based suggestions
    trends = performance_stats.get('trends', {})
    if 'short_term' in trends:
        trend_direction = trends['short_term'].get('direction')
        if trend_direction == 'declining':
            suggestions.append("📉 Performance declining in recent messages:")
            suggestions.append("  • Review recent query patterns for issues")
            suggestions.append("  • Consider simplifying current approach")
        elif trend_direction == 'improving':
            suggestions.append("📈 Performance improving! Keep up the good work.")
    
    return suggestions

# Authentication event handlers with comprehensive performance monitoring
def on_user_login(username: str):
    """Handle user login - initialize user-specific session with comprehensive performance monitoring."""
    switch_user_context(username)
    
    # Initialize performance monitor and analyzer for new session
    user_perf_key = f"user_{username}_performance_monitor"
    user_analyzer_key = f"user_{username}_chat_analyzer"
    
    if user_perf_key not in st.session_state:
        st.session_state[user_perf_key] = PerformanceMonitor()
    
    if user_analyzer_key not in st.session_state:
        st.session_state[user_analyzer_key] = ChatPerformanceAnalyzer()
    
    logging.info(f"✅ User {username} logged in with performance monitoring enabled")

def on_user_logout(username: str):
    """Handle user logout with comprehensive performance data archival and cleanup."""
    # Archive performance data before clearing
    user_perf_key = f"user_{username}_performance_monitor"
    user_analyzer_key = f"user_{username}_chat_analyzer"
    
    performance_monitor = st.session_state.get(user_perf_key)
    chat_analyzer = st.session_state.get(user_analyzer_key)
    
    if performance_monitor:
        # Get final comprehensive performance summary
        final_stats = performance_monitor.get_performance_summary()
        tool_analysis = performance_monitor.get_tool_performance_analysis()
        
        # Log comprehensive session performance summary
        logging.info(f"📊 Session performance summary for {username}:")
        logging.info(f"  - Session duration: {final_stats.get('session_duration_minutes', 0):.1f} minutes")
        logging.info(f"  - Total messages: {final_stats.get('total_messages', 0)}")
        logging.info(f"  - Successful messages: {final_stats.get('successful_messages', 0)}")
        logging.info(f"  - Success rate: {final_stats.get('success_rate', 0):.1f}%")
        logging.info(f"  - Average processing time: {final_stats.get('average_processing_time', 0):.2f}s")
        logging.info(f"  - Performance grade: {final_stats.get('performance_grade', 'N/A')}")
        logging.info(f"  - Efficiency score: {final_stats.get('efficiency_score', 0):.1f}")
        logging.info(f"  - Tool executions: {final_stats.get('total_tool_executions', 0)}")
        logging.info(f"  - Tool success rate: {final_stats.get('tool_success_rate', 0):.1f}%")
        
        # Save session summary to file (optional)
        try:
            session_summary = {
                'username': username,
                'logout_timestamp': datetime.now().isoformat(),
                'performance_stats': final_stats,
                'tool_analysis': tool_analysis.get('tools', {}) if tool_analysis.get('status') == 'success' else {}
            }
            
            # Create performance logs directory if it doesn't exist
            logs_dir = "performance_logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Save summary (optional - comment out if not needed)
            # summary_file = os.path.join(logs_dir, f"session_{username}_{int(time.time())}.json")
            # with open(summary_file, 'w') as f:
            #     json.dump(session_summary, f, indent=2)
            
        except Exception as e:
            logging.error(f"Error saving session summary: {str(e)}")
    
    # Continue with standard logout process
    clear_user_session_data(username)
    
    # Clear global session state
    keys_to_clear = ["params", "current_chat_id", "current_chat_index", 
                     "history_chats", "messages", "conversation_memory"]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Disconnect from MCP servers on logout
    try:
        logging.info(f"🔌 Disconnecting from MCP servers for user logout: {username}")
        disconnect_from_mcp_servers(logout_context=True)
        
        # Clear MCP-related session state
        mcp_keys_to_clear = ["client", "agent", "tools", "servers", "system_prompt", 
                           "system_prompt_is_custom", "tool_executions"]
        
        for key in mcp_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        logging.info(f"✅ Successfully disconnected MCP servers for user: {username}")
        
    except Exception as e:
        logging.error(f"❌ Error disconnecting MCP servers during logout: {str(e)}")
    
    logging.info(f"🚪 User {username} logged out with performance data archived")

# Export functions for external use
__all__ = [
    'PerformanceMonitor',
    'ChatPerformanceAnalyzer', 
    'ChatService',
    'init_session',
    'get_user_history',
    'switch_user_context',
    'get_current_chat',
    '_append_message_to_session',
    'append_tool_execution_message',
    'create_chat',
    'switch_chat',
    'delete_chat',
    'get_conversation_summary',
    'get_clean_conversation_memory',
    'clear_user_session_data',
    'get_user_performance_stats',
    'get_user_performance_trends',
    'get_chat_performance_comparison',
    'get_user_chat_stats',
    'get_messages_by_type',
    'get_performance_suggestions',
    'on_user_login',
    'on_user_logout'
]