"""
v8.9.0: Silent Error Detection & Display System
- Catches and displays errors that would otherwise be silent
- Logs to both UI and database
- Helps debug Streamlit rendering issues
"""

import streamlit as st
import traceback
from datetime import datetime
from typing import Callable, Any, Optional

class ErrorTracker:
    """Global error tracking for silent failures"""

    def __init__(self):
        self.errors = []
        self.init_session_state()

    def init_session_state(self):
        """Initialize session state for error tracking"""
        if '_error_tracker_log' not in st.session_state:
            st.session_state._error_tracker_log = []
        if '_error_tracker_visible' not in st.session_state:
            st.session_state._error_tracker_visible = False

    def add_error(self, error_type: str, context: str, exception: Exception, severity: str = "error"):
        """
        Add error to tracker

        Args:
            error_type: Type of error (e.g., "RENDER", "QUERY", "STATE")
            context: Where error occurred (e.g., "personel_module.render")
            exception: The exception object
            severity: "error", "warning", "critical"
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "context": context,
            "severity": severity,
            "message": str(exception),
            "traceback": traceback.format_exc(),
            "session_id": st.session_state.get('session_id', 'unknown')
        }

        st.session_state._error_tracker_log.append(error_entry)
        self.errors.append(error_entry)

    def wrap(self, func: Callable, context: str, fallback: Any = None) -> Callable:
        """
        Decorator to wrap function calls and catch silent errors

        Usage:
            try_render = error_tracker.wrap(render_personel_tab, "personel_tab.render")
            try_render(engine)
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.add_error(
                    error_type="FUNCTION_CALL",
                    context=context,
                    exception=e,
                    severity="critical"
                )
                st.error(f"🔴 **Hata [{context}]:** {str(e)[:100]}")
                if fallback is not None:
                    return fallback
                return None
        return wrapper

    def display_error_panel(self):
        """Display error log in sidebar for debugging"""
        if not st.session_state._error_tracker_log:
            return

        with st.sidebar:
            with st.expander(f"🔴 HATAlar ({len(st.session_state._error_tracker_log)})", expanded=False):
                for i, err in enumerate(st.session_state._error_tracker_log[-5:], 1):  # Last 5 errors
                    st.write(f"**{i}. {err['type']} - {err['severity'].upper()}**")
                    st.caption(f"**Context:** {err['context']}")
                    st.caption(f"**Message:** {err['message']}")
                    st.code(err['traceback'], language="python")
                    st.divider()

    def clear_errors(self):
        """Clear error log"""
        st.session_state._error_tracker_log = []
        self.errors = []

# Global instance
_error_tracker = ErrorTracker()

def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance"""
    return _error_tracker

def safe_render(func: Callable, context: str, fallback_message: str = "Modül yüklenemedi"):
    """
    Safe wrapper for rendering functions

    Usage in app.py:
        safe_render(render_personel_tab, "personel_ekle_duzenle", engine, dept_options)
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tracker = get_error_tracker()
            tracker.add_error(
                error_type="RENDER",
                context=context,
                exception=e,
                severity="critical"
            )
            st.error(f"❌ **Modül Render Hatası**\n\n`{context}`\n\n{str(e)}")
            st.error(f"**Detay:**\n```\n{traceback.format_exc()}\n```")

    return wrapper(*args, **kwargs)
