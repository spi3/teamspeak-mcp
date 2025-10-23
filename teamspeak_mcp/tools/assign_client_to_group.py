import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_assign_client_to_group_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def assign_client_to_group(
        client_database_id: int, action: str, group_id: int
    ) -> str:
        """
        Add or remove a client from a server group
        Args:
            - client_database_id: Client database ID to modify group membership for
            - action: Action to perform (add, remove)
            - group_id: Server group ID to add/remove client from
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if action == "add":
                ts_connection.connection.servergroupaddclient(
                    sgid=group_id,
                    cldbid=client_database_id,
                )
                result = (
                    f"✅ Client {client_database_id} added to server group {group_id}"
                )
            elif action == "remove":
                ts_connection.connection.servergroupdelclient(
                    sgid=group_id,
                    cldbid=client_database_id,
                )
                result = f"✅ Client {client_database_id} removed from server group {group_id}"
            else:
                raise ValueError(f"Unknown action: {action}")

            return result
        except Exception as e:
            raise Exception(f"Error managing client group membership: {e}")
