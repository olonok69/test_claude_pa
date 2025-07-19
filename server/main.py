from mcp.server.fastmcp import FastMCP

# Import strategy modules
from strategies.bollinger_fibonacci import register_bollinger_fibonacci_tools
from strategies.macd_donchian import register_macd_donchian_tools
from strategies.connors_zscore import register_connors_zscore_tools
from strategies.dual_moving_average import register_dual_ma_tools
from strategies.bollinger_zscore import register_bollinger_zscore_tools

# Initialize FastMCP server
mcp = FastMCP("finance tools", "1.0.0")

# Register all strategy tools
register_bollinger_fibonacci_tools(mcp)
register_macd_donchian_tools(mcp)
register_connors_zscore_tools(mcp)
register_dual_ma_tools(mcp)
register_bollinger_zscore_tools(mcp)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')