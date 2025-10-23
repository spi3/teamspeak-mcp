import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_list_bans_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def list_bans() -> str:
        """
        List all active ban rules on the virtual server
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.banlist()

            # Extract bans list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                bans = response.parsed
            else:
                # Fallback to container emulation
                bans = list(response)

            result = "📋 **Active Ban Rules:**\n\n"
            for ban in bans:
                ban_id = ban.get("banid", "N/A")
                ip = ban.get("ip", "N/A")
                name = ban.get("name", "N/A")
                uid = ban.get("uid", "N/A")
                time = ban.get("time", "N/A")
                reason = ban.get("reason", "N/A")
                result += f"• **ID**: {ban_id}\n"
                result += f"   - IP: {ip}\n"
                result += f"   - Name: {name}\n"
                result += f"   - UID: {uid}\n"
                result += f"   - Duration: {time} seconds\n"
                result += f"   - Reason: {reason}\n\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving ban rules: {e}")
