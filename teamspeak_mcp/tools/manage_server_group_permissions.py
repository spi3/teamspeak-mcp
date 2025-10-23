import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_manage_server_group_permissions_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def manage_server_group_permissions(
        group_id: int,
        action: str,
        permission: Optional[str] = None,
        value: Optional[int] = None,
        skip: bool = False,
        negate: bool = False,
    ) -> str:
        """
        Add, remove or list permissions for a server group
        Args:
            - group_id: Server group ID to modify permissions for
            - action: Action to perform (add, remove, list)
            - permission: Permission name (required for add/remove actions)
            - value: Permission value (required for add action)
            - skip: Skip flag for permission (optional, default: false)
            - negate: Negate flag for permission (optional, default: false)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if action == "add":
                if not permission or value is None:
                    raise ValueError(
                        "Permission name and value required for add action"
                    )

                ts_connection.connection.servergroupaddperm(
                    sgid=group_id,
                    permsid=permission,
                    permvalue=value,
                )
                result = f"✅ Permission '{permission}' added to server group {group_id} with value {value}"
            elif action == "remove":
                if not permission:
                    raise ValueError("Permission name required for remove action")

                ts_connection.connection.servergroupdelperm(
                    sgid=group_id,
                    permsid=permission,
                )
                result = (
                    f"✅ Permission '{permission}' removed from server group {group_id}"
                )
            elif action == "list":
                perms_response = ts_connection.connection.servergrouppermlist(
                    sgid=group_id,
                    permsid=True,
                )

                if hasattr(perms_response, "parsed"):
                    perms = perms_response.parsed
                else:
                    perms = list(perms_response)

                result = f"📋 **Server Group {group_id} Permissions:**\n\n"
                if perms:
                    for perm in perms:
                        perm_name = perm.get("permsid", "N/A")
                        perm_value = perm.get("permvalue", "N/A")
                        result += f"• **{perm_name}**: {perm_value}\n"
                else:
                    result += "No custom permissions set for this server group."
            else:
                raise ValueError(f"Unknown action: {action}")

            return result
        except Exception as e:
            raise Exception(f"Error managing server group permissions: {e}")
