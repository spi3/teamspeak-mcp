import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_send_private_message_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def send_private_message(client_id: int, message: str) -> str:
        """
        Send a private message to a user
        Args:
            - client_id: Target client ID
            - message: Message to send
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.sendtextmessage(
                targetmode=1,
                target=client_id,
                msg=message,
            )

            return f"✅ Private message sent to client {client_id}: {message}"
        except Exception as e:
            raise Exception(f"Error sending private message: {e}")
