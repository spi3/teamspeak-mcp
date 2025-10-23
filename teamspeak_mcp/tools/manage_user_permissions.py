import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_manage_user_permissions_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def manage_user_permissions(
        client_id: int,
        action: str,
        group_id: Optional[int] = None,
        permission: Optional[str] = None,
        value: Optional[int] = None,
        skip: bool = False,
        negate: bool = False,
    ) -> str:
        """
        Manage user permissions: add/remove server groups, set individual permissions
        Args:
            - client_id: Client ID to manage permissions for
            - action: Action to perform (add_group, remove_group, list_groups, add_permission, remove_permission, list_permissions)
            - group_id: Server group ID (required for add_group/remove_group actions)
            - permission: Permission name (required for add_permission/remove_permission actions)
            - value: Permission value (required for add_permission action)
            - skip: Skip flag for permission (optional, default: false)
            - negate: Negate flag for permission (optional, default: false)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            # First, get client database ID for some operations
            client_info = None
            if action in [
                "list_groups",
                "add_permission",
                "remove_permission",
                "list_permissions",
            ]:
                client_info_response = ts_connection.connection.clientinfo(
                    clid=client_id
                )

                if (
                    hasattr(client_info_response, "parsed")
                    and client_info_response.parsed
                ):
                    client_info = client_info_response.parsed[0]
                elif hasattr(client_info_response, "__getitem__"):
                    client_info = client_info_response[0]
                else:
                    raise Exception("Could not get client info")

            if action == "add_group":
                if not group_id:
                    raise ValueError("Server group ID required for add_group action")

                # Get client database ID first
                client_info_response = ts_connection.connection.clientinfo(
                    clid=client_id
                )

                if (
                    hasattr(client_info_response, "parsed")
                    and client_info_response.parsed
                ):
                    client_info = client_info_response.parsed[0]
                elif hasattr(client_info_response, "__getitem__"):
                    client_info = client_info_response[0]
                else:
                    raise Exception("Could not get client info")

                client_database_id = client_info.get("client_database_id")
                if not client_database_id:
                    raise ValueError("Could not get client database ID")

                ts_connection.connection.servergroupaddclient(
                    sgid=group_id,
                    cldbid=client_database_id,
                )
                result = f"✅ Client {client_id} added to server group {group_id}"

            elif action == "remove_group":
                if not group_id:
                    raise ValueError("Server group ID required for remove_group action")

                # Get client database ID first
                client_info_response = ts_connection.connection.clientinfo(
                    clid=client_id
                )

                if (
                    hasattr(client_info_response, "parsed")
                    and client_info_response.parsed
                ):
                    client_info = client_info_response.parsed[0]
                elif hasattr(client_info_response, "__getitem__"):
                    client_info = client_info_response[0]
                else:
                    raise Exception("Could not get client info")

                client_database_id = client_info.get("client_database_id")
                if not client_database_id:
                    raise ValueError("Could not get client database ID")

                ts_connection.connection.servergroupdelclient(
                    sgid=group_id,
                    cldbid=client_database_id,
                )
                result = f"✅ Client {client_id} removed from server group {group_id}"

            elif action == "list_groups":
                # Use the client database ID to get server groups
                client_database_id = client_info.get("client_database_id")
                if not client_database_id:
                    raise ValueError("Could not get client database ID")

                groups_response = ts_connection.connection.servergroupsbyclientid(
                    cldbid=client_database_id,
                )

                if hasattr(groups_response, "parsed"):
                    groups = groups_response.parsed
                else:
                    groups = list(groups_response)

                result = f"📋 **Client {client_id} Server Groups:**\n\n"
                if groups:
                    for group in groups:
                        group_name = group.get("name", "N/A")
                        group_id = group.get("sgid", "N/A")
                        result += f"• **{group_name}** (ID: {group_id})\n"
                else:
                    result += "No server groups assigned to this client."

            elif action == "add_permission":
                if not permission or value is None:
                    raise ValueError(
                        "Permission name and value required for add_permission action"
                    )

                client_database_id = client_info.get("client_database_id")
                if not client_database_id:
                    raise ValueError("Could not get client database ID")

                ts_connection.connection.clientaddperm(
                    cldbid=client_database_id,
                    permsid=permission,
                    permvalue=value,
                    permskip=skip,
                )
                result = f"✅ Permission '{permission}' added to client {client_id} with value {value}"

            elif action == "remove_permission":
                if not permission:
                    raise ValueError(
                        "Permission name required for remove_permission action"
                    )

                client_database_id = client_info.get("client_database_id")
                if not client_database_id:
                    raise ValueError("Could not get client database ID")

                ts_connection.connection.clientdelperm(
                    cldbid=client_database_id,
                    permsid=permission,
                )
                result = f"✅ Permission '{permission}' removed from client {client_id}"

            elif action == "list_permissions":
                client_database_id = client_info.get("client_database_id")
                if not client_database_id:
                    raise ValueError("Could not get client database ID")

                perms_response = ts_connection.connection.clientpermlist(
                    cldbid=client_database_id,
                    permsid=True,
                )

                if hasattr(perms_response, "parsed"):
                    perms = perms_response.parsed
                else:
                    perms = list(perms_response)

                result = f"📋 **Client {client_id} Permissions:**\n\n"
                if perms:
                    for perm in perms:
                        perm_name = perm.get("permsid", "N/A")
                        perm_value = perm.get("permvalue", "N/A")
                        result += f"• **{perm_name}**: {perm_value}\n"
                else:
                    result += "No custom permissions assigned to this client."

            else:
                raise ValueError(f"Unknown action: {action}")

            return result
        except Exception as e:
            raise Exception(f"Error managing user permissions: {e}")
