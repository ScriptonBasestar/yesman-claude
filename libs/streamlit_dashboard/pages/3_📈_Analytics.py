"""Analytics and monitoring page"""

import streamlit as st
import sys
from pathlib import Path
import time
import json
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from libs.core.session_manager import SessionManager
from libs.core.claude_manager import ClaudeManager

st.set_page_config(
    page_title="Analytics & Monitoring",
    page_icon="📈",
    layout="wide"
)

def initialize_managers():
    """Initialize session state managers"""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    if 'claude_manager' not in st.session_state:
        st.session_state.claude_manager = ClaudeManager()

def render_overview_metrics():
    """Render overview metrics"""
    try:
        sessions = st.session_state.session_manager.get_all_sessions()
        
        # Calculate metrics
        total_sessions = len(sessions)
        running_sessions = len([s for s in sessions if s.status == 'running'])
        total_windows = sum(len(s.windows) for s in sessions)
        total_panes = sum(len(w.panes) for w in s.windows for s in sessions)
        
        # Controller metrics
        active_controllers = 0
        waiting_controllers = 0
        
        for session in sessions:
            try:
                controller = st.session_state.claude_manager.get_controller(session.session_name)
                if controller:
                    if controller.is_running:
                        active_controllers += 1
                    if controller.is_waiting_for_input():
                        waiting_controllers += 1
            except Exception:
                pass
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", total_sessions)
            st.metric("Running Sessions", running_sessions, delta=running_sessions-total_sessions+running_sessions)
        
        with col2:
            st.metric("Total Windows", total_windows)
            st.metric("Total Panes", total_panes)
        
        with col3:
            st.metric("Active Controllers", active_controllers)
            st.metric("Waiting for Input", waiting_controllers)
        
        with col4:
            uptime_hours = 24  # Placeholder - could track actual uptime
            st.metric("Dashboard Uptime", f"{uptime_hours}h")
            current_time = datetime.now().strftime("%H:%M:%S")
            st.metric("Current Time", current_time)
        
        return sessions
        
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return []

def render_session_status_chart(sessions):
    """Render session status distribution"""
    if not sessions:
        return
    
    st.subheader("📊 Session Status Distribution")
    
    # Count sessions by status
    status_counts = {}
    for session in sessions:
        status = session.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Display as metrics
    col1, col2 = st.columns(2)
    
    with col1:
        for status, count in status_counts.items():
            color = "🟢" if status == "running" else "🔴"
            st.write(f"{color} **{status.title()}**: {count} sessions")
    
    with col2:
        # Show percentage
        total = len(sessions)
        for status, count in status_counts.items():
            percentage = (count / total) * 100 if total > 0 else 0
            st.write(f"**{status.title()}**: {percentage:.1f}%")

def render_controller_analytics(sessions):
    """Render controller analytics"""
    st.subheader("🎮 Controller Analytics")
    
    controller_stats = {
        'total': 0,
        'active': 0,
        'ready': 0,
        'waiting': 0,
        'error': 0
    }
    
    model_usage = {}
    auto_next_count = 0
    
    for session in sessions:
        try:
            controller = st.session_state.claude_manager.get_controller(session.session_name)
            if controller:
                controller_stats['total'] += 1
                
                if controller.is_running:
                    controller_stats['active'] += 1
                else:
                    controller_stats['ready'] += 1
                
                if controller.is_waiting_for_input():
                    controller_stats['waiting'] += 1
                
                # Model usage
                model = controller.selected_model
                model_usage[model] = model_usage.get(model, 0) + 1
                
                # Auto next setting
                if controller.is_auto_next_enabled:
                    auto_next_count += 1
            
        except Exception:
            controller_stats['error'] += 1
    
    # Display controller stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Controller Status:**")
        st.write(f"• Active: {controller_stats['active']}")
        st.write(f"• Ready: {controller_stats['ready']}")
        st.write(f"• Waiting for Input: {controller_stats['waiting']}")
        st.write(f"• Errors: {controller_stats['error']}")
    
    with col2:
        st.write("**Settings:**")
        st.write(f"• Auto Next Enabled: {auto_next_count}")
        st.write("**Model Usage:**")
        for model, count in model_usage.items():
            st.write(f"• {model.title()}: {count}")

def render_response_history():
    """Render aggregated response history"""
    st.subheader("📜 Response History Summary")
    
    try:
        sessions = st.session_state.session_manager.get_all_sessions()
        all_responses = []
        
        for session in sessions:
            try:
                controller = st.session_state.claude_manager.get_controller(session.session_name)
                if controller:
                    history = controller.get_response_history()
                    for entry in history:
                        entry['session'] = session.session_name
                        all_responses.append(entry)
            except Exception:
                pass
        
        if not all_responses:
            st.info("No response history available")
            return
        
        # Sort by timestamp (most recent first)
        all_responses.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Show summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Responses", len(all_responses))
        
        with col2:
            # Count unique prompt types
            prompt_types = set(entry['prompt_type'] for entry in all_responses)
            st.metric("Prompt Types", len(prompt_types))
        
        with col3:
            # Count responses in last hour (placeholder)
            recent_count = len([r for r in all_responses[:10]])  # Simplified
            st.metric("Recent Responses", recent_count)
        
        # Response type breakdown
        st.write("**Response Type Breakdown:**")
        type_counts = {}
        for entry in all_responses:
            ptype = entry['prompt_type']
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        for ptype, count in type_counts.items():
            st.write(f"• {ptype}: {count}")
        
        # Recent responses table
        st.write("**Recent Responses:**")
        
        # Show last 10 responses
        for entry in all_responses[:10]:
            with st.expander(f"{entry['timestamp']} - {entry['session']} - {entry['prompt_type']}"):
                st.write(f"**Response:** {entry['response']}")
                if 'content_snippet' in entry:
                    st.code(entry['content_snippet'], language="text")
    
    except Exception as e:
        st.error(f"Error loading response history: {e}")

def render_collection_stats():
    """Render content collection statistics"""
    st.subheader("📁 Content Collection Statistics")
    
    try:
        sessions = st.session_state.session_manager.get_all_sessions()
        total_files = 0
        total_size_mb = 0
        
        collection_by_session = []
        
        for session in sessions:
            try:
                controller = st.session_state.claude_manager.get_controller(session.session_name)
                if controller:
                    stats = controller.get_collection_stats()
                    files = stats.get('total_files', 0)
                    size = stats.get('total_size_mb', 0)
                    
                    if files > 0:
                        collection_by_session.append({
                            'session': session.session_name,
                            'files': files,
                            'size_mb': size
                        })
                        
                        total_files += files
                        total_size_mb += size
            except Exception:
                pass
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Files Collected", total_files)
        
        with col2:
            st.metric("Total Size", f"{total_size_mb:.1f} MB")
        
        with col3:
            avg_size = total_size_mb / total_files if total_files > 0 else 0
            st.metric("Average File Size", f"{avg_size:.2f} MB")
        
        # Per-session breakdown
        if collection_by_session:
            st.write("**Collection by Session:**")
            
            for item in collection_by_session:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**{item['session']}**")
                with col2:
                    st.write(f"{item['files']} files")
                with col3:
                    st.write(f"{item['size_mb']:.1f} MB")
        else:
            st.info("No content collection data available")
    
    except Exception as e:
        st.error(f"Error loading collection stats: {e}")

def main():
    """Main analytics page"""
    initialize_managers()
    
    st.title("📈 Analytics & Monitoring")
    st.write("Real-time analytics and performance monitoring for Yesman Claude")
    
    # Auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    
    with col2:
        auto_refresh = st.checkbox("Auto Refresh (5s)", value=True)
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    st.divider()
    
    # Overview metrics
    st.subheader("📊 Overview")
    sessions = render_overview_metrics()
    
    st.divider()
    
    # Charts and analytics
    col1, col2 = st.columns(2)
    
    with col1:
        render_session_status_chart(sessions)
    
    with col2:
        render_controller_analytics(sessions)
    
    st.divider()
    
    # Detailed analytics
    col1, col2 = st.columns(2)
    
    with col1:
        render_response_history()
    
    with col2:
        render_collection_stats()
    
    # Auto refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()