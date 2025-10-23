import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_create_channel_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def create_channel(
        name: str, parent_id: Optional[int] = 0, permanent: bool = False
    ) -> str:
        """
        Create a new channel
        Args:
            - name: Channel name
            - parent_id: Parent channel ID (optional)
            - permanent: Permanent or temporary channel (default: temporary)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            channel_type = 1 if permanent else 0
            result = ts_connection.connection.channelcreate(
                channel_name=name,
                channel_flag_permanent=permanent,
                cpid=parent_id,
            )

            return f"✅ Channel '{name}' created successfully"
        except Exception as e:
            raise Exception(f"Error creating channel: {e}")
