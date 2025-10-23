import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_list_server_groups_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def list_server_groups() -> str:
        """
        List all server groups available on the virtual server
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.servergrouplist()

            # Extract groups list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                groups = response.parsed
            else:
                # Fallback to container emulation
                groups = list(response)

            result = "👥 **Server Groups:**\n\n"
            for group in groups:
                group_id = group.get("sgid", "N/A")
                group_name = group.get("name", "N/A")
                group_type = group.get("type", "N/A")
                result += f"• **ID {group_id}**: {group_name} (Type: {group_type})\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving server groups: {e}")
