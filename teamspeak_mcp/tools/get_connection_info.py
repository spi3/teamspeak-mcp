import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_get_connection_info_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def get_connection_info() -> str:
        """
        Get detailed connection information for the virtual server
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.serverinfo()

            # Extract the first (and usually only) result
            if hasattr(response, "parsed") and response.parsed:
                info = response.parsed[0]
            elif hasattr(response, "__getitem__"):
                # Use container emulation
                info = response[0]
            else:
                raise Exception("Unexpected response format")

            result = "🖥️ **Server Connection Information:**\n\n"
            for key, value in info.items():
                result += f"• **{key}**: {value}\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving connection info: {e}")
