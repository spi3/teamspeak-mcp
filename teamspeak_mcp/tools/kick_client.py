import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_kick_client_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def kick_client(
        client_id: int, reason: str = "Expelled by AI", from_server: bool = False
    ) -> str:
        """
        Kick a client from server or channel
        Args:
            - client_id: Client ID
            - reason: Kick reason
            - from_server: Kick from server (true) or channel (false)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            kick_type = 5 if from_server else 4  # 5 = server, 4 = channel
            ts_connection.connection.clientkick(
                clid=client_id,
                reasonid=kick_type,
                reasonmsg=reason,
            )

            location = "from server" if from_server else "from channel"
            return f"✅ Client {client_id} kicked {location}: {reason}"
        except Exception as e:
            raise Exception(f"Error kicking client: {e}")
