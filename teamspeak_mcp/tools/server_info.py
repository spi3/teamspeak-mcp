import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_server_info_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def server_info() -> str:
        """
        Get TeamSpeak server information
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.serverinfo()

            # Extract the first (and usually only) result
            if hasattr(response, "parsed") and response.parsed:
                info = response.parsed[0]
            elif hasattr(response, "__getitem__"):
                # Use container emulation
                info = response[0]
            else:
                raise Exception("Unexpected response format")

            result = "🖥️ **TeamSpeak Server Information:**\n\n"
            result += f"• **Name**: {info.get('virtualserver_name', 'N/A')}\n"
            result += f"• **Version**: {info.get('virtualserver_version', 'N/A')}\n"
            result += f"• **Platform**: {info.get('virtualserver_platform', 'N/A')}\n"
            result += f"• **Clients**: {info.get('virtualserver_clientsonline', 'N/A')}/{info.get('virtualserver_maxclients', 'N/A')}\n"
            result += (
                f"• **Uptime**: {info.get('virtualserver_uptime', 'N/A')} seconds\n"
            )
            result += f"• **Port**: {info.get('virtualserver_port', 'N/A')}\n"
            result += f"• **Created**: {info.get('virtualserver_created', 'N/A')}\n"
            result += f"• **Auto Start**: {'Yes' if info.get('virtualserver_autostart') == '1' else 'No'}\n"
            result += (
                f"• **Machine ID**: {info.get('virtualserver_machine_id', 'N/A')}\n"
            )
            result += f"• **Unique ID**: {info.get('virtualserver_unique_identifier', 'N/A')}\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving server info: {e}")
