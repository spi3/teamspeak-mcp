import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_search_clients_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def search_clients(pattern: str, search_by_uid: bool = False) -> str:
        """
        Search for clients by name pattern or unique identifier
        Args:
            - pattern: Search pattern for client name or UID
            - search_by_uid: Search by unique identifier instead of name (default: false)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if search_by_uid:
                response = ts_connection.connection.clientdbfind(
                    pattern=pattern, uid=True
                )
            else:
                response = ts_connection.connection.clientfind(pattern=pattern)

            # Extract clients list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                clients = response.parsed
            else:
                # Fallback to container emulation
                clients = list(response)

            result = f"👥 **Search Results for '{pattern}':**\n\n"
            if not clients:
                result += "No clients found matching the pattern."
            else:
                for client in clients:
                    if search_by_uid:
                        client_id = client.get("cldbid", "N/A")
                        nickname = client.get("client_nickname", "N/A")
                        result += f"• **DB ID {client_id}**: {nickname}\n"
                    else:
                        client_id = client.get("clid", "N/A")
                        nickname = client.get("client_nickname", "N/A")
                        result += f"• **ID {client_id}**: {nickname}\n"

            return result
        except Exception as e:
            raise Exception(f"Error searching for clients: {e}")
