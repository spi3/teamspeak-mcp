import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_move_client_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def move_client(client_id: int, channel_id: int) -> str:
        """
        Move a client to another channel
        Args:
            - client_id: Client ID
            - channel_id: Destination channel ID
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.clientmove(clid=client_id, cid=channel_id)

            return f"✅ Client {client_id} moved to channel {channel_id}"
        except Exception as e:
            raise Exception(f"Error moving client: {e}")
