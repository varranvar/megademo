"""Template MCP Server.

Replace this docstring with your tool's description.
"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("template-tool", log_level="WARNING")


@server.tool()
def example_tool(package_name: str) -> str:
    """Describe what this tool does.

    Args:
        package_name: The name of the Ubuntu/Debian package to analyse.
    """
    # TODO: implement analysis
    return f"Analysis for {package_name} not yet implemented."


def main():
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
