import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_add_log_entry_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def add_log_entry(log_level: int, message: str) -> str:
        """
        Add a custom entry to the server log
        Args:
            - log_level: Log level (1=ERROR, 2=WARNING, 3=DEBUG, 4=INFO)
            - message: Log message to add
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.logadd(loglevel=log_level, message=message)
            return f"✅ Log entry added successfully"
        except Exception as e:
            raise Exception(f"Error adding log entry: {e}")
