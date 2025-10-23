import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_update_channel_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def update_channel(
        channel_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        password: Optional[str] = None,
        max_clients: Optional[int] = None,
        talk_power: Optional[int] = None,
        codec_quality: Optional[int] = None,
        permanent: Optional[bool] = None,
    ) -> str:
        """
        Update channel properties (name, description, password, talk power, limits, etc.)
        Args:
            - channel_id: Channel ID to update
            - name: New channel name (optional)
            - description: New channel description (optional)
            - password: New channel password (optional, empty string to remove)
            - max_clients: Maximum number of clients (optional)
            - talk_power: Required talk power to speak in channel (optional)
            - codec_quality: Audio codec quality 1-10 (optional)
            - permanent: Make channel permanent (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        # Build kwargs dict with only non-None values
        kwargs = {"cid": channel_id}

        if name:
            kwargs["channel_name"] = name
        if description:
            kwargs["channel_description"] = description
        if password is not None:
            kwargs["channel_password"] = password
        if max_clients:
            kwargs["channel_maxclients"] = max_clients
        if talk_power is not None:
            kwargs["channel_needed_talk_power"] = talk_power
        if codec_quality:
            kwargs["channel_codec_quality"] = codec_quality
        if permanent is not None:
            kwargs["channel_flag_permanent"] = 1 if permanent else 0

        try:
            ts_connection.connection.channeledit(**kwargs)

            changes = [k.replace("channel_", "") for k in kwargs.keys() if k != "cid"]
            result = f"✅ Channel {channel_id} updated successfully\n"
            result += f"📝 Modified properties: {', '.join(changes)}"

            return result
        except Exception as e:
            raise Exception(f"Error updating channel: {e}")
