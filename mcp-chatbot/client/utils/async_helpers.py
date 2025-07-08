import streamlit as st
import asyncio
import logging

# Helper function for running async functions
def run_async(coro):
    """Run an async function within the stored event loop with error handling."""
    try:
        if "loop" not in st.session_state or st.session_state.loop is None:
            st.session_state.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.loop)
        
        loop = st.session_state.loop
        
        # Check if the loop is running
        if loop.is_running():
            # If the loop is already running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=30)  # 30 second timeout
        else:
            return loop.run_until_complete(coro)
            
    except Exception as e:
        logging.error(f"Error running async function: {str(e)}")
        st.error(f"❌ Async operation failed: {str(e)}")
        return None

def safe_reset_connection_state():
    """Safely reset all connection-related session state variables."""
    try:
        # Get the current client safely
        client = st.session_state.get("client")
        
        if client is not None:
            try:
                # Attempt to close the client properly
                print("🔄 Closing existing MCP client...")
                close_coro = client.__aexit__(None, None, None)
                run_async(close_coro)
                print("✅ MCP client closed successfully")
            except Exception as e:
                print(f"⚠️  Warning: Error closing previous client: {str(e)}")
                # Continue anyway, don't fail the reset
        
        # Reset connection state variables
        connection_keys = ["client", "agent", "tools"]
        for key in connection_keys:
            if key in st.session_state:
                st.session_state[key] = None if key == "client" or key == "agent" else []
        
        print("🔄 Connection state reset successfully")
        
    except Exception as e:
        logging.error(f"Error resetting connection state: {str(e)}")
        print(f"⚠️  Warning: Error during connection reset: {str(e)}")
        
        # Force reset even if there were errors
        st.session_state["client"] = None
        st.session_state["agent"] = None
        st.session_state["tools"] = []

def reset_connection_state():
    """Reset all connection-related session state variables (public interface)."""
    safe_reset_connection_state()

def safe_shutdown():
    """Safely shutdown connections with error handling."""
    try:
        client = st.session_state.get("client")
        if client is not None:
            try:
                print("🚪 Shutting down MCP client...")
                close_coro = client.__aexit__(None, None, None)
                run_async(close_coro)
                print("✅ MCP client shutdown complete")
            except Exception as e:
                print(f"⚠️  Warning: Error during shutdown: {str(e)}")
        
        # Clean up session state
        if "loop" in st.session_state and st.session_state.loop:
            try:
                loop = st.session_state.loop
                if not loop.is_closed():
                    # Cancel any pending tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    
                    # Close the loop if it's not running
                    if not loop.is_running():
                        loop.close()
                        
                st.session_state.loop = None
                print("✅ Event loop cleanup complete")
            except Exception as e:
                print(f"⚠️  Warning: Error cleaning up event loop: {str(e)}")
                
    except Exception as e:
        logging.error(f"Error during safe shutdown: {str(e)}")
        print(f"⚠️  Warning: Error during safe shutdown: {str(e)}")

def on_shutdown():
    """Cleanup function called on application shutdown."""
    safe_shutdown()

def check_authentication():
    """Check if user is authenticated and redirect if not."""
    # Check authentication status from session state
    authentication_status = st.session_state.get("authentication_status")
    
    if authentication_status is None:
        st.warning("🔐 Please authenticate to access this feature.")
        st.info("👈 Use the sidebar to log in")
        st.stop()
    elif authentication_status is False:
        st.error("❌ Authentication failed. Please check your credentials.")
        st.stop()
    # If authentication_status is True, user is authenticated and can proceed
    return True

def initialize_event_loop():
    """Initialize the event loop if it doesn't exist."""
    try:
        if "loop" not in st.session_state or st.session_state.loop is None:
            st.session_state.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.loop)
            print("✅ Event loop initialized")
        return True
    except Exception as e:
        logging.error(f"Error initializing event loop: {str(e)}")
        print(f"❌ Error initializing event loop: {str(e)}")
        return False

def handle_provider_change():
    """Handle provider change with proper cleanup and error handling."""
    try:
        print("🔄 Handling provider change...")
        
        # Reset connections safely
        safe_reset_connection_state()
        
        # Clear any cached AI model instances
        if "llm_instance" in st.session_state:
            del st.session_state["llm_instance"]
        
        # Clear any tool executions
        if "tool_executions" in st.session_state:
            st.session_state["tool_executions"] = []
        
        print("✅ Provider change handled successfully")
        
    except Exception as e:
        logging.error(f"Error handling provider change: {str(e)}")
        st.error(f"❌ Error changing provider: {str(e)}")
        
        # Force reset in case of error
        st.session_state["client"] = None
        st.session_state["agent"] = None
        st.session_state["tools"] = []

def safe_async_operation(coro, operation_name="operation"):
    """Safely execute an async operation with proper error handling."""
    try:
        print(f"🔄 Starting {operation_name}...")
        result = run_async(coro)
        
        if result is not None:
            print(f"✅ {operation_name} completed successfully")
            return result
        else:
            print(f"⚠️  {operation_name} returned None")
            return None
            
    except Exception as e:
        logging.error(f"Error in {operation_name}: {str(e)}")
        print(f"❌ Error in {operation_name}: {str(e)}")
        return None

def cleanup_session_state():
    """Clean up session state to prevent memory leaks."""
    try:
        # List of keys that should be cleaned up
        cleanup_keys = [
            "llm_instance",
            "model_cache",
            "connection_cache"
        ]
        
        for key in cleanup_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        print("✅ Session state cleanup complete")
        
    except Exception as e:
        logging.error(f"Error during session state cleanup: {str(e)}")
        print(f"⚠️  Warning: Error during session state cleanup: {str(e)}")

def get_connection_status():
    """Get current connection status safely."""
    try:
        return {
            "client_connected": st.session_state.get("client") is not None,
            "agent_available": st.session_state.get("agent") is not None,
            "tools_count": len(st.session_state.get("tools", [])),
            "loop_active": st.session_state.get("loop") is not None
        }
    except Exception as e:
        logging.error(f"Error getting connection status: {str(e)}")
        return {
            "client_connected": False,
            "agent_available": False,
            "tools_count": 0,
            "loop_active": False,
            "error": str(e)
        }