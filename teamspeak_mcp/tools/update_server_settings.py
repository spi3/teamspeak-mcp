import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_update_server_settings_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def update_server_settings(
        name: Optional[str] = None,
        welcome_message: Optional[str] = None,
        max_clients: Optional[int] = None,
        password: Optional[str] = None,
        hostmessage: Optional[str] = None,
        hostmessage_mode: Optional[int] = None,
        default_server_group: Optional[int] = None,
        default_channel_group: Optional[int] = None,
    ) -> str:
        """
        Update virtual server settings (name, welcome message, max clients, etc.)
        Args:
            - name: Server name (optional)
            - welcome_message: Server welcome message (optional)
            - max_clients: Maximum number of clients (optional)
            - password: Server password (optional, empty string to remove)
            - hostmessage: Host message displayed in server info (optional)
            - hostmessage_mode: Host message mode: 0=none, 1=log, 2=modal, 3=modalquit (optional)
            - default_server_group: Default server group ID for new clients (optional)
            - default_channel_group: Default channel group ID for new clients (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            kwargs = {}
            if name:
                kwargs["virtualserver_name"] = name
            if welcome_message:
                kwargs["virtualserver_welcomemessage"] = welcome_message
            if max_clients:
                kwargs["virtualserver_maxclients"] = max_clients
            if password:
                kwargs["virtualserver_password"] = password
            if hostmessage:
                kwargs["virtualserver_hostmessage"] = hostmessage
                if hostmessage_mode is not None:
                    kwargs["virtualserver_hostmessage_mode"] = hostmessage_mode
            if default_server_group:
                kwargs["virtualserver_default_server_group"] = default_server_group
            if default_channel_group:
                kwargs["virtualserver_default_channel_group"] = default_channel_group

            ts_connection.connection.serveredit(**kwargs)

            changes = [k for k, v in kwargs.items() if v is not None]
            result = f"✅ Server settings updated successfully\n"
            result += f"📝 Modified properties: {', '.join(changes)}"

            return result
        except Exception as e:
            raise Exception(f"Error updating server settings: {e}")
