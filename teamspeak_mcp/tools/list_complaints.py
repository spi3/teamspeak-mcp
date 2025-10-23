import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_list_complaints_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def list_complaints(target_client_database_id: Optional[int] = None) -> str:
        """
        List complaints on the virtual server
        Args:
            - target_client_database_id: Target client database ID to filter complaints (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.complaintlist()

            # Extract complaints list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                complaints = response.parsed
            else:
                # Fallback to container emulation
                complaints = list(response)

            result = "📋 **Complaints:**\n\n"
            for complaint in complaints:
                complaint_id = complaint.get("complaintid", "N/A")
                client_database_id = complaint.get("cldbid", "N/A")
                reason = complaint.get("reason", "N/A")
                result += f"• **ID**: {complaint_id}\n"
                result += f"   - Client ID: {client_database_id}\n"
                result += f"   - Reason: {reason}\n\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving complaints: {e}")
