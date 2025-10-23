import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_get_file_info_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def get_file_info(
        channel_id: int, file_path: str, channel_password: Optional[str] = None
    ) -> str:
        """
        Get detailed information about a specific file in a channel
        Args:
            - channel_id: Channel ID containing the file
            - file_path: Full path to the file
            - channel_password: Channel password if required (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.ftgetfileinfo(
                cid=channel_id,
                name=file_path,
                cpw=channel_password if channel_password else "",
            )

            # Extract file info - response.parsed is a list of dictionaries
            if hasattr(response, "parsed") and response.parsed:
                info = response.parsed[0]
            else:
                # Fallback to container emulation
                info = response[0] if response else {}

            result = f"📄 **File Information for '{file_path}':**\n\n"
            for key, value in info.items():
                # Format key for better readability
                display_key = key.replace("_", " ").title()
                result += f"• **{display_key}**: {value}\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving file info: {e}")
