import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_manage_ban_rules_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def manage_ban_rules(
        action: str,
        ban_id: Optional[int] = None,
        ip: Optional[str] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        time: int = 0,
        reason: str = "Banned by AI",
    ) -> str:
        """
        Create, delete or manage ban rules
        Args:
            - action: Action to perform (add, delete, delete_all)
            - ban_id: Ban ID (required for delete action)
            - ip: IP address pattern to ban (optional for add action)
            - name: Name pattern to ban (optional for add action)
            - uid: Client unique identifier to ban (optional for add action)
            - time: Ban duration in seconds (0 = permanent, default: 0)
            - reason: Ban reason (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if action == "add":
                ts_connection.connection.banadd(
                    ip=ip,
                    name=name,
                    uid=uid,
                    time=time,
                    reason=reason,
                )
                result = f"✅ Ban rule added successfully"
            elif action == "delete":
                if not ban_id:
                    raise ValueError("Ban ID required for delete action")

                ts_connection.connection.bandel(banid=ban_id)
                result = f"✅ Ban rule {ban_id} deleted successfully"
            elif action == "delete_all":
                ts_connection.connection.bandelall()
                result = "✅ All ban rules deleted successfully"
            else:
                raise ValueError(f"Unknown action: {action}")

            return result
        except Exception as e:
            raise Exception(f"Error managing ban rules: {e}")
