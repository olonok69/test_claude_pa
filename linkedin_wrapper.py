#!/usr/bin/env python3
"""
LinkedIn MCP Server Wrapper
This wrapper ensures the environment is properly set up
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set up logging to stderr so it appears in Claude Desktop logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

def main():
    """Main wrapper function"""
    try:
        # Change to the script directory
        os.chdir(current_dir)
        logger.info(f"Changed working directory to: {current_dir}")
        
        # Set environment variables if not already set
        if not os.getenv("LINKEDIN_USERNAME"):
            # Replace with your actual credentials
            os.environ["LINKEDIN_USERNAME"] = "olonok@gmail.com"
            logger.info("Set LINKEDIN_USERNAME from wrapper")
        
        if not os.getenv("LINKEDIN_PASSWORD"):
            # Replace with your actual password
            os.environ["LINKEDIN_PASSWORD"] = "Larisa10@"
            logger.info("Set LINKEDIN_PASSWORD from wrapper")
        
        # Enable debug mode
        os.environ["DEBUG_MODE"] = "true"
        
        # Import and run the main server
        logger.info("Starting LinkedIn MCP Server...")
        from linkedin_server import mcp
        mcp.run()
        
    except Exception as e:
        logger.error(f"Wrapper failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()