# ui_components/performance_dashboard.py - New component for comprehensive performance monitoring

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

def create_performance_dashboard():
    """Create a comprehensive performance monitoring dashboard."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        st.warning("🔐 Please authenticate to access the performance dashboard")
        return
    
    st.header("📊 Performance Dashboard")
    st.markdown(f"Performance analytics for **{current_user}**")
    
    # Get performance data
    from services.chat_service import get_user_performance_stats, get_user_performance_trends, get_chat_performance_comparison
    
    perf_stats = get_user_performance_stats(current_user)
    perf_trends = get_user_performance_trends(current_user)
    chat_comparison = get_chat_performance_comparison(current_user)
    
    # Create dashboard sections
    create_performance_overview(perf_stats)
    create_performance_trends_section(perf_trends, perf_stats)
    create_chat_comparison_section(chat_comparison)
    create_performance_recommendations(perf_stats)

def create_performance_overview(perf_stats: Dict[str, Any]):
    """Create performance overview section with key metrics."""
    st.subheader("🎯 Performance Overview")
    
    if perf_stats.get('status') != 'active':
        st.info("No performance data available yet. Start chatting to see analytics!")
        return
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        grade = perf_stats.get('performance_grade', 'N/A')
        grade_color = get_grade_color(grade)
        st.metric(
            "Performance Grade", 
            grade,
            help="Overall performance grade (A+ to D) based on speed and accuracy"
        )
        if grade != 'N/A':
            st.markdown(f'<p style="color: {grade_color}; font-size: 0.8em; margin-top: -10px;">●●●</p>', unsafe_allow_html=True)
    
    with col2:
        avg_time = perf_stats.get('average_processing_time', 0)
        st.metric(
            "Avg Response Time", 
            f"{avg_time:.2f}s",
            help="Average time for AI to respond to your messages"
        )
    
    with col3:
        total_messages = perf_stats.get('total_messages', 0)
        st.metric(
            "Total Messages", 
            total_messages,
            help="Total number of messages processed in this session"
        )
    
    with col4:
        error_rate = perf_stats.get('error_rate', 0)
        st.metric(
            "Error Rate", 
            f"{error_rate:.1f}%",
            help="Percentage of messages that resulted in errors"
        )
    
    with col5:
        efficiency = perf_stats.get('messages_per_minute', 0)
        st.metric(
            "Messages/Min", 
            f"{efficiency:.1f}",
            help="Average messages processed per minute"
        )
    
    # Detailed metrics in expandable section
    with st.expander("📈 Detailed Performance Metrics", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Response Time Analysis:**")
            st.write(f"• Fastest response: {perf_stats.get('min_processing_time', 0):.2f}s")
            st.write(f"• Slowest response: {perf_stats.get('max_processing_time', 0):.2f}s")
            st.write(f"• Median response: {perf_stats.get('median_processing_time', 0):.2f}s")
            st.write(f"• Standard deviation: {perf_stats.get('std_dev_processing_time', 0):.2f}s")
        
        with col2:
            st.markdown("**Session Information:**")
            session_duration = perf_stats.get('session_duration_minutes', 0)
            st.write(f"• Session duration: {session_duration:.1f} minutes")
            st.write(f"• Total processing time: {perf_stats.get('total_processing_time', 0):.1f}s")
            st.write(f"• Tool executions: {perf_stats.get('tool_executions', 0)}")
            st.write(f"• Estimated tokens: {perf_stats.get('estimated_tokens_processed', 0):,}")

def create_performance_trends_section(perf_trends: Dict[str, Any], perf_stats: Dict[str, Any]):
    """Create performance trends visualization section."""
    st.subheader("📈 Performance Trends")
    
    # Get current user's messages for trend analysis
    current_user = st.session_state.get('username')
    user_messages_key = f"user_{current_user}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    # Extract processing times
    processing_data = []
    for i, msg in enumerate(messages):
        if msg.get('processing_time') and msg.get('role') == 'assistant':
            processing_data.append({
                'message_number': i + 1,
                'processing_time': msg['processing_time'],
                'timestamp': msg.get('timestamp', ''),
                'content_length': len(msg.get('content', '')),
                'is_error': msg.get('is_error', False)
            })
    
    if len(processing_data) < 2:
        st.info("Need at least 2 messages to show performance trends.")
        return
    
    # Create trend visualization
    fig = create_processing_time_chart(processing_data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend analysis
    if perf_trends.get('status') == 'active':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trend_direction = perf_trends.get('trend_direction', 'stable')
            trend_magnitude = perf_trends.get('trend_magnitude_percent', 0)
            
            if trend_direction == 'improving':
                st.success(f"📈 Performance Improving: {trend_magnitude:.1f}% faster")
            elif trend_direction == 'declining':
                st.warning(f"📉 Performance Declining: {trend_magnitude:.1f}% slower")
            else:
                st.info("➡️ Performance Stable")
        
        with col2:
            recent_avg = perf_trends.get('recent_average', 0)
            st.metric("Recent Average", f"{recent_avg:.2f}s")
        
        with col3:
            previous_avg = perf_trends.get('previous_average', 0)
            st.metric("Previous Average", f"{previous_avg:.2f}s")

def create_processing_time_chart(processing_data: List[Dict]) -> go.Figure:
    """Create an interactive processing time chart."""
    fig = go.Figure()
    
    # Processing time line
    fig.add_trace(go.Scatter(
        x=[d['message_number'] for d in processing_data],
        y=[d['processing_time'] for d in processing_data],
        mode='lines+markers',
        name='Processing Time',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6),
        hovertemplate='<b>Message %{x}</b><br>' +
                      'Processing Time: %{y:.2f}s<br>' +
                      '<extra></extra>'
    ))
    
    # Add trend line
    message_numbers = [d['message_number'] for d in processing_data]
    processing_times = [d['processing_time'] for d in processing_data]
    
    if len(processing_times) > 1:
        # Simple linear trend
        import numpy as np
        z = np.polyfit(message_numbers, processing_times, 1)
        trend_line = np.poly1d(z)
        
        fig.add_trace(go.Scatter(
            x=message_numbers,
            y=trend_line(message_numbers),
            mode='lines',
            name='Trend',
            line=dict(color='red', width=1, dash='dash'),
            hovertemplate='Trend Line<extra></extra>'
        ))
    
    # Mark errors
    error_messages = [d for d in processing_data if d['is_error']]
    if error_messages:
        fig.add_trace(go.Scatter(
            x=[d['message_number'] for d in error_messages],
            y=[d['processing_time'] for d in error_messages],
            mode='markers',
            name='Errors',
            marker=dict(color='red', size=10, symbol='x'),
            hovertemplate='<b>Error in Message %{x}</b><br>' +
                          'Processing Time: %{y:.2f}s<br>' +
                          '<extra></extra>'
        ))
    
    # Add performance threshold lines
    fast_threshold = st.session_state.get('fast_threshold', 2.0)
    slow_threshold = st.session_state.get('slow_threshold', 5.0)
    
    fig.add_hline(y=fast_threshold, line_dash="dot", line_color="green", 
                  annotation_text="Fast Threshold")
    fig.add_hline(y=slow_threshold, line_dash="dot", line_color="orange", 
                  annotation_text="Slow Threshold")
    
    fig.update_layout(
        title="Processing Time Trends",
        xaxis_title="Message Number",
        yaxis_title="Processing Time (seconds)",
        hovermode='closest',
        height=400
    )
    
    return fig

def create_chat_comparison_section(chat_comparison: Dict[str, Any]):
    """Create chat performance comparison section."""
    st.subheader("💬 Chat Performance Comparison")
    
    if chat_comparison.get('status') != 'success':
        st.info("No chat comparison data available.")
        return
    
    # Overall chat statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Chats", chat_comparison.get('total_chats', 0))
    
    with col2:
        st.metric("Total Messages", chat_comparison.get('total_messages', 0))
    
    with col3:
        overall_avg = chat_comparison.get('overall_average', 0)
        st.metric("Overall Avg Time", f"{overall_avg:.2f}s")
    
    with col4:
        total_time = chat_comparison.get('total_processing_time', 0)
        st.metric("Total Processing Time", f"{total_time:.1f}s")
    
    # Best and worst performing chats
    col1, col2 = st.columns(2)
    
    with col1:
        best_chat = chat_comparison.get('best_performing_chat')
        if best_chat:
            st.success("🏆 Best Performing Chat")
            st.write(f"**{best_chat['chat_name']}**")
            st.write(f"Average: {best_chat['average_processing_time']:.2f}s")
            st.write(f"Messages: {best_chat['message_count']}")
    
    with col2:
        worst_chat = chat_comparison.get('worst_performing_chat')
        if worst_chat:
            st.warning("🐌 Slowest Chat")
            st.write(f"**{worst_chat['chat_name']}**")
            st.write(f"Average: {worst_chat['average_processing_time']:.2f}s")
            st.write(f"Messages: {worst_chat['message_count']}")
    
    # Detailed chat comparison table
    if st.checkbox("Show detailed chat comparison"):
        chat_details = chat_comparison.get('chat_details', [])
        if chat_details:
            # Sort by average processing time
            sorted_chats = sorted(chat_details, key=lambda x: x['average_processing_time'])
            
            st.markdown("**Chat Performance Ranking:**")
            for i, chat in enumerate(sorted_chats[:10]):  # Show top 10
                rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    
                    with col1:
                        st.write(rank_emoji)
                    
                    with col2:
                        st.write(f"**{chat['chat_name'][:30]}**")
                    
                    with col3:
                        st.write(f"{chat['average_processing_time']:.2f}s avg")
                    
                    with col4:
                        st.write(f"{chat['message_count']} messages")

def create_performance_recommendations(perf_stats: Dict[str, Any]):
    """Create performance recommendations section."""
    st.subheader("💡 Performance Recommendations")
    
    if perf_stats.get('status') != 'active':
        st.info("No performance data available for recommendations.")
        return
    
    from services.chat_service import get_performance_suggestions
    suggestions = get_performance_suggestions(perf_stats)
    
    if not suggestions:
        st.success("✅ No specific recommendations - your performance looks good!")
        return
    
    # Display recommendations
    for suggestion in suggestions:
        if suggestion.startswith('✅'):
            st.success(suggestion)
        elif suggestion.startswith('⚠️') or suggestion.startswith('🚨'):
            st.warning(suggestion)
        elif suggestion.startswith('💡') or suggestion.startswith('🔧'):
            st.info(suggestion)
        else:
            st.write(suggestion)
    
    # Performance optimization tips
    with st.expander("🚀 Performance Optimization Tips", expanded=False):
        st.markdown("""
        **General Tips for Better Performance:**
        
        **Query Optimization:**
        - Be specific in your database queries
        - Use table names and column names when known
        - Break complex requests into smaller parts
        
        **Tool Usage:**
        - Use `list_tables` to explore database schema first
        - Use `describe_table` to understand table structure
        - Use `get_table_sample` to see example data
        
        **Communication:**
        - Be clear and specific in your requests
        - Provide context when asking follow-up questions
        - Ask one main question at a time for faster responses
        
        **Error Prevention:**
        - Double-check table and column names
        - Use proper SQL syntax for your database type
        - Verify data types before complex operations
        """)

def get_grade_color(grade: str) -> str:
    """Get color for performance grade."""
    grade_colors = {
        'A+': '#00C851',
        'A': '#2BBBAD',
        'B': '#FF8800',
        'C': '#FF6600',
        'D': '#FF3547',
        'N/A': '#6c757d'
    }
    return grade_colors.get(grade, '#6c757d')

def export_performance_data():
    """Export comprehensive performance data."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    from services.chat_service import get_user_performance_stats, get_chat_performance_comparison
    import json
    
    # Gather all performance data
    perf_stats = get_user_performance_stats(current_user)
    chat_comparison = get_chat_performance_comparison(current_user)
    
    # Get message-level data
    user_messages_key = f"user_{current_user}_messages"
    messages = st.session_state.get(user_messages_key, [])
    
    message_performance = []
    for i, msg in enumerate(messages):
        if msg.get('processing_time'):
            message_performance.append({
                'message_number': i + 1,
                'role': msg.get('role'),
                'processing_time': msg.get('processing_time'),
                'content_length': len(msg.get('content', '')),
                'timestamp': msg.get('timestamp'),
                'is_error': msg.get('is_error', False)
            })
    
    export_data = {
        'performance_export': {
            'user': current_user,
            'exported_at': datetime.now().isoformat(),
            'session_performance': perf_stats,
            'chat_comparison': chat_comparison,
            'message_performance': message_performance,
            'export_version': '1.0'
        }
    }
    
    json_str = json.dumps(export_data, indent=2)
    
    st.download_button(
        label="📊 Download Performance Data",
        data=json_str,
        file_name=f"performance_data_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

# Integration function for adding performance dashboard to main app
def add_performance_dashboard_to_sidebar():
    """Add performance dashboard link to sidebar."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Performance")
    
    if st.sidebar.button("📈 Performance Dashboard", use_container_width=True):
        st.session_state['show_performance_dashboard'] = True
        st.rerun()
    
    # Quick performance summary in sidebar
    from services.chat_service import get_user_performance_stats
    perf_stats = get_user_performance_stats(current_user)
    
    if perf_stats.get('status') == 'active':
        grade = perf_stats.get('performance_grade', 'N/A')
        avg_time = perf_stats.get('average_processing_time', 0)
        
        with st.sidebar.container():
            st.markdown(f"**Grade:** {grade}")
            st.markdown(f"**Avg Time:** {avg_time:.2f}s")
            
            # Quick export
            if st.button("📊 Export Data", key="quick_export_perf", use_container_width=True):
                export_performance_data()