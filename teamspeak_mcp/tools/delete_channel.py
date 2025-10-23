import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_delete_channel_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def delete_channel(channel_id: int, force: bool = False) -> str:
        """
        Delete a channel
        Args:
            - channel_id: Channel ID to delete
            - force: Force deletion even if clients are present
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.channeldelete(
                cid=channel_id,
                force=1 if force else 0,
            )

            return f"✅ Channel {channel_id} deleted successfully"
        except Exception as e:
            raise Exception(f"Error deleting channel: {e}")
