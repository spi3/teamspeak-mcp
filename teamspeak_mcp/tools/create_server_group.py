import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_create_server_group_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def create_server_group(name: str, type: int = 1) -> str:
        """
        Create a new server group with specified name and type
        Args:
            - name: Name for the new server group
            - type: Group type (0=template, 1=regular, 2=query, default: 1)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.servergroupadd(name=name, type_=type)

            # Try to extract the new group ID from response
            result = f"✅ Server group '{name}' created successfully"
            if hasattr(response, "parsed") and response.parsed:
                group_info = response.parsed[0]
                if "sgid" in group_info:
                    result += f" (ID: {group_info['sgid']})"

            return result
        except Exception as e:
            raise Exception(f"Error creating server group: {e}")
