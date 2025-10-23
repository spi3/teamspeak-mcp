import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_poke_client_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def poke_client(client_id: int, message: str) -> str:
        """
        Send a poke (alert notification) to a client - more attention-grabbing than a private message
        Args:
            - client_id: Target client ID to poke
            - message: Poke message to send
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.clientpoke(clid=client_id, msg=message)

            return f"👉 Poke sent to client {client_id}: {message}"
        except Exception as e:
            raise Exception(f"Error sending poke: {e}")
