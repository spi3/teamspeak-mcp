import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_find_channels_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def find_channels(pattern: str) -> str:
        """
        Search for channels by name pattern
        Args:
            - pattern: Search pattern for channel name
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.channelfind(pattern=pattern)

            # Extract channels list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                channels = response.parsed
            else:
                # Fallback to container emulation
                channels = list(response)

            result = f"📋 **Channel Search Results for '{pattern}':**\n\n"
            if not channels:
                result += "No channels found matching the pattern."
            else:
                for channel in channels:
                    channel_id = channel.get("cid", "N/A")
                    channel_name = channel.get("channel_name", "N/A")
                    result += f"• **ID {channel_id}**: {channel_name}\n"

            return result
        except Exception as e:
            raise Exception(f"Error searching for channels: {e}")
