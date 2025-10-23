import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_client_info_detailed_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def client_info_detailed(client_id: int) -> str:
        """
        Get detailed information about a specific client
        Args:
            - client_id: Client ID to get detailed info for
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.clientinfo(clid=client_id)

            # Extract the first (and usually only) result
            if hasattr(response, "parsed") and response.parsed:
                info = response.parsed[0]
            elif hasattr(response, "__getitem__"):
                # Use container emulation
                info = response[0]
            else:
                raise Exception("Unexpected response format")

            result = "👤 **Client Information:**\n\n"

            # Basic identification
            result += f"• **ID**: {info.get('clid', 'N/A')}\n"
            result += f"• **Database ID**: {info.get('client_database_id', 'N/A')}\n"
            result += f"• **Nickname**: {info.get('client_nickname', 'N/A')}\n"

            # Unique identifier (truncate if too long)
            unique_id = info.get("client_unique_identifier", "N/A")
            if unique_id != "N/A" and len(str(unique_id)) > 32:
                unique_id = str(unique_id)[:32] + "..."
            result += f"• **Unique ID**: {unique_id}\n"

            # Location and channel
            result += f"• **Channel ID**: {info.get('cid', 'N/A')}\n"

            # Client capabilities and status
            result += f"• **Talk Power**: {info.get('client_talk_power', '0')}\n"
            result += f"• **Client Type**: {'ServerQuery' if info.get('client_type') == '1' else 'Regular'}\n"
            result += f"• **Platform**: {info.get('client_platform', 'N/A')}\n"
            result += f"• **Version**: {info.get('client_version', 'N/A')}\n"

            # Status information
            result += (
                f"• **Away**: {'Yes' if info.get('client_away') == '1' else 'No'}\n"
            )
            result += f"• **Away Message**: {info.get('client_away_message', 'N/A')}\n"

            # Audio status
            result += f"• **Input Muted**: {'Yes' if info.get('client_input_muted') == '1' else 'No'}\n"
            result += f"• **Output Muted**: {'Yes' if info.get('client_output_muted') == '1' else 'No'}\n"
            result += f"• **Input Hardware**: {'Yes' if info.get('client_input_hardware') == '1' else 'No'}\n"
            result += f"• **Output Hardware**: {'Yes' if info.get('client_output_hardware') == '1' else 'No'}\n"

            # Timing information
            result += f"• **Created**: {info.get('client_created', 'N/A')}\n"
            result += (
                f"• **Last Connected**: {info.get('client_lastconnected', 'N/A')}\n"
            )
            result += f"• **Connection Time**: {info.get('connection_connected_time', 'N/A')}ms\n"

            # Geographic information
            result += f"• **Country**: {info.get('client_country', 'N/A')}\n"
            result += f"• **IP Address**: {info.get('connection_client_ip', 'N/A')}\n"
            result += f"• **Idle Time**: {info.get('client_idle_time', 'N/A')}ms\n"
            result += f"• **Is Recording**: {'Yes' if info.get('client_is_recording') == '1' else 'No'}\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving client info: {e}")
