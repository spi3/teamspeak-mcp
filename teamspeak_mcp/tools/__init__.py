from mcp.server.fastmcp import FastMCP
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection

# Import all tool creation functions
from .send_channel_message import create_send_channel_message_tool
from .send_private_message import create_send_private_message_tool
from .poke_client import create_poke_client_tool
from .list_clients import create_list_clients_tool
from .list_channels import create_list_channels_tool
from .create_channel import create_create_channel_tool
from .delete_channel import create_delete_channel_tool
from .move_client import create_move_client_tool
from .kick_client import create_kick_client_tool
from .ban_client import create_ban_client_tool
from .server_info import create_server_info_tool
from .update_channel import create_update_channel_tool
from .set_channel_talk_power import create_set_channel_talk_power_tool
from .channel_info import create_channel_info_tool
from .manage_channel_permissions import create_manage_channel_permissions_tool
from .client_info_detailed import create_client_info_detailed_tool
from .update_server_settings import create_update_server_settings_tool
from .manage_user_permissions import create_manage_user_permissions_tool
from .diagnose_permissions import create_diagnose_permissions_tool
from .list_server_groups import create_list_server_groups_tool
from .assign_client_to_group import create_assign_client_to_group_tool
from .create_server_group import create_create_server_group_tool
from .manage_server_group_permissions import create_manage_server_group_permissions_tool
from .list_bans import create_list_bans_tool
from .manage_ban_rules import create_manage_ban_rules_tool
from .list_complaints import create_list_complaints_tool
from .search_clients import create_search_clients_tool
from .find_channels import create_find_channels_tool
from .list_privilege_tokens import create_list_privilege_tokens_tool
from .create_privilege_token import create_create_privilege_token_tool
from .list_files import create_list_files_tool
from .get_file_info import create_get_file_info_tool
from .manage_file_permissions import create_manage_file_permissions_tool
from .view_server_logs import create_view_server_logs_tool
from .add_log_entry import create_add_log_entry_tool
from .get_connection_info import create_get_connection_info_tool
from .create_server_snapshot import create_create_server_snapshot_tool
from .deploy_server_snapshot import create_deploy_server_snapshot_tool
from .get_instance_logs import create_get_instance_logs_tool

# Export all tool creation functions
__all__ = [
    "create_send_channel_message_tool",
    "create_send_private_message_tool",
    "create_poke_client_tool",
    "create_list_clients_tool",
    "create_list_channels_tool",
    "create_create_channel_tool",
    "create_delete_channel_tool",
    "create_move_client_tool",
    "create_kick_client_tool",
    "create_ban_client_tool",
    "create_server_info_tool",
    "create_update_channel_tool",
    "create_set_channel_talk_power_tool",
    "create_channel_info_tool",
    "create_manage_channel_permissions_tool",
    "create_client_info_detailed_tool",
    "create_update_server_settings_tool",
    "create_manage_user_permissions_tool",
    "create_diagnose_permissions_tool",
    "create_list_server_groups_tool",
    "create_assign_client_to_group_tool",
    "create_create_server_group_tool",
    "create_manage_server_group_permissions_tool",
    "create_list_bans_tool",
    "create_manage_ban_rules_tool",
    "create_list_complaints_tool",
    "create_search_clients_tool",
    "create_find_channels_tool",
    "create_list_privilege_tokens_tool",
    "create_create_privilege_token_tool",
    "create_list_files_tool",
    "create_get_file_info_tool",
    "create_manage_file_permissions_tool",
    "create_view_server_logs_tool",
    "create_add_log_entry_tool",
    "create_get_connection_info_tool",
    "create_create_server_snapshot_tool",
    "create_deploy_server_snapshot_tool",
    "create_get_instance_logs_tool",
    "register_all_tools",
]


def register_all_tools(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:
    """Register all TeamSpeak tools with the FastMCP server."""
    create_send_channel_message_tool(mcp, ts_connection)
    create_send_private_message_tool(mcp, ts_connection)
    create_poke_client_tool(mcp, ts_connection)
    create_list_clients_tool(mcp, ts_connection)
    create_list_channels_tool(mcp, ts_connection)
    create_create_channel_tool(mcp, ts_connection)
    create_delete_channel_tool(mcp, ts_connection)
    create_move_client_tool(mcp, ts_connection)
    create_kick_client_tool(mcp, ts_connection)
    create_ban_client_tool(mcp, ts_connection)
    create_server_info_tool(mcp, ts_connection)
    create_update_channel_tool(mcp, ts_connection)
    create_set_channel_talk_power_tool(mcp, ts_connection)
    create_channel_info_tool(mcp, ts_connection)
    create_manage_channel_permissions_tool(mcp, ts_connection)
    create_client_info_detailed_tool(mcp, ts_connection)
    create_update_server_settings_tool(mcp, ts_connection)
    create_manage_user_permissions_tool(mcp, ts_connection)
    create_diagnose_permissions_tool(mcp, ts_connection)
    create_list_server_groups_tool(mcp, ts_connection)
    create_assign_client_to_group_tool(mcp, ts_connection)
    create_create_server_group_tool(mcp, ts_connection)
    create_manage_server_group_permissions_tool(mcp, ts_connection)
    create_list_bans_tool(mcp, ts_connection)
    create_manage_ban_rules_tool(mcp, ts_connection)
    create_list_complaints_tool(mcp, ts_connection)
    create_search_clients_tool(mcp, ts_connection)
    create_find_channels_tool(mcp, ts_connection)
    create_list_privilege_tokens_tool(mcp, ts_connection)
    create_create_privilege_token_tool(mcp, ts_connection)
    create_list_files_tool(mcp, ts_connection)
    create_get_file_info_tool(mcp, ts_connection)
    create_manage_file_permissions_tool(mcp, ts_connection)
    create_view_server_logs_tool(mcp, ts_connection)
    create_add_log_entry_tool(mcp, ts_connection)
    create_get_connection_info_tool(mcp, ts_connection)
    create_create_server_snapshot_tool(mcp, ts_connection)
    create_deploy_server_snapshot_tool(mcp, ts_connection)
    create_get_instance_logs_tool(mcp, ts_connection)
