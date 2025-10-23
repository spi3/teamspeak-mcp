import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_ban_client_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def ban_client(
        client_id: int, reason: str = "Banned by AI", duration: int = 0
    ) -> str:
        """
        Ban a client from the server
        Args:
            - client_id: Client ID
            - reason: Ban reason
            - duration: Ban duration in seconds (0 = permanent)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.banclient(
                clid=client_id,
                time=duration,
                banreason=reason,
            )

            duration_text = (
                "permanently" if duration == 0 else f"for {duration} seconds"
            )
            return f"✅ Client {client_id} banned {duration_text}: {reason}"
        except Exception as e:
            raise Exception(f"Error banning client: {e}")
