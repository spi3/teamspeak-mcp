import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_send_channel_message_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def send_channel_message(channel_id: int, message: str) -> str:
        """
        Send a message to a TeamSpeak channel
        Args:
            - channel_id: Channel ID (optional, uses current channel if not specified)
            - message: The message to send
        Returns:
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if channel_id:
                ts_connection.connection.sendtextmessage(
                    targetmode=2, target=channel_id, msg=message
                )
            else:
                ts_connection.connection.sendtextmessage(
                    targetmode=2, target=0, msg=message
                )

            return f"✅ Message sent to channel: {message}"
        except Exception as e:
            raise Exception(f"Error sending message: {e}")
