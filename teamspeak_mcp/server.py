"""
TeamSpeak MCP Server - Allows controlling TeamSpeak from AI models.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import ts3
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
from pydantic import BaseModel

# Logging configuration - ensure all logs go to stderr for MCP protocol compliance
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TeamSpeak MCP Server")
    parser.add_argument("--host", default=os.getenv("TEAMSPEAK_HOST", "localhost"),
                       help="TeamSpeak server host")
    parser.add_argument("--port", type=int, default=int(os.getenv("TEAMSPEAK_PORT", "10011")),
                       help="TeamSpeak ServerQuery port")
    parser.add_argument("--user", default=os.getenv("TEAMSPEAK_USER", "serveradmin"),
                       help="TeamSpeak ServerQuery username")
    parser.add_argument("--password", default=os.getenv("TEAMSPEAK_PASSWORD", ""),
                       help="TeamSpeak ServerQuery password")
    parser.add_argument("--server-id", type=int, default=int(os.getenv("TEAMSPEAK_SERVER_ID", "1")),
                       help="TeamSpeak virtual server ID")
    return parser.parse_args()

class TeamSpeakConnection:
    """TeamSpeak connection manager."""
    
    def __init__(self, host=None, port=None, user=None, password=None, server_id=None):
        # Use provided arguments or fall back to environment variables
        self.connection: Optional[ts3.query.TS3Connection] = None
        self.host = host or os.getenv("TEAMSPEAK_HOST", "localhost")
        self.port = port or int(os.getenv("TEAMSPEAK_PORT", "10011"))
        self.user = user or os.getenv("TEAMSPEAK_USER", "serveradmin")
        self.password = password or os.getenv("TEAMSPEAK_PASSWORD", "")
        self.server_id = server_id or int(os.getenv("TEAMSPEAK_SERVER_ID", "1"))
        
    async def connect(self) -> bool:
        """Connect to TeamSpeak server."""
        try:
            # Use asyncio.to_thread for blocking operations
            self.connection = await asyncio.to_thread(ts3.query.TS3Connection, self.host, self.port)
            await asyncio.to_thread(self.connection.use, sid=self.server_id)
            
            # Authenticate if password is provided
            if self.password:
                # First try to login with username/password (classic ServerQuery auth)
                try:
                    await asyncio.to_thread(self.connection.login, client_login_name=self.user, client_login_password=self.password)
                    logger.info("Successfully authenticated with username/password")
                except Exception as login_error:
                    logger.info(f"Username/password authentication failed: {login_error}")
                    
                    # If login fails, try to use as admin token
                    try:
                        await asyncio.to_thread(self.connection.tokenuse, token=self.password)
                        logger.info("Successfully used admin privilege key")
                    except Exception as token_error:
                        logger.warning(f"Could not use admin token either: {token_error}")
                        logger.warning("Continuing with basic anonymous permissions")
            else:
                logger.info("No password provided, using anonymous connection")
            
            # Test basic connectivity and permissions
            try:
                # Try a simple command to verify permissions
                await asyncio.to_thread(self.connection.whoami)
                logger.info("Basic connectivity test passed")
            except Exception as test_error:
                logger.warning(f"Basic connectivity test failed: {test_error}")
            
            logger.info("TeamSpeak connection established successfully")
            return True
        except Exception as e:
            logger.error(f"TeamSpeak connection error: {e}")
            self.connection = None
            return False
    
    async def disconnect(self):
        """Disconnect from TeamSpeak server."""
        if self.connection:
            try:
                await asyncio.to_thread(self.connection.quit)
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connection = None
                logger.info("TeamSpeak disconnected")
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connection is not None

# Global connection instance - will be initialized in main()
ts_connection = None

# MCP Tools definition
TOOLS = [
    Tool(
        name="connect_to_server",
        description="Connect to the configured TeamSpeak server",
        inputSchema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    ),
    Tool(
        name="send_channel_message",
        description="Send a message to a TeamSpeak channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID (optional, uses current channel if not specified)",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send",
                },
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="send_private_message",
        description="Send a private message to a user",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Target client ID",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send",
                },
            },
            "required": ["client_id", "message"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="poke_client",
        description="Send a poke (alert notification) to a client - more attention-grabbing than a private message",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Target client ID to poke",
                },
                "message": {
                    "type": "string",
                    "description": "Poke message to send",
                },
            },
            "required": ["client_id", "message"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="list_clients",
        description="List all clients connected to the server",
        inputSchema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    ),
    Tool(
        name="list_channels",
        description="List all channels on the server",
        inputSchema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    ),
    Tool(
        name="create_channel",
        description="Create a new channel",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Channel name",
                },
                "parent_id": {
                    "type": "integer",
                    "description": "Parent channel ID (optional)",
                },
                "permanent": {
                    "type": "boolean",
                    "description": "Permanent or temporary channel (default: temporary)",
                    "default": False,
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="delete_channel",
        description="Delete a channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to delete",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force deletion even if clients are present",
                    "default": False,
                },
            },
            "required": ["channel_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="move_client",
        description="Move a client to another channel",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID",
                },
                "channel_id": {
                    "type": "integer",
                    "description": "Destination channel ID",
                },
            },
            "required": ["client_id", "channel_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="kick_client",
        description="Kick a client from server or channel",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID",
                },
                "reason": {
                    "type": "string",
                    "description": "Kick reason",
                    "default": "Expelled by AI",
                },
                "from_server": {
                    "type": "boolean",
                    "description": "Kick from server (true) or channel (false)",
                    "default": False,
                },
            },
            "required": ["client_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="ban_client",
        description="Ban a client from the server",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID",
                },
                "reason": {
                    "type": "string",
                    "description": "Ban reason",
                    "default": "Banned by AI",
                },
                "duration": {
                    "type": "integer",
                    "description": "Ban duration in seconds (0 = permanent)",
                    "default": 0,
                },
            },
            "required": ["client_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="server_info",
        description="Get TeamSpeak server information",
        inputSchema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    ),
    Tool(
        name="update_channel",
        description="Update channel properties (name, description, password, talk power, limits, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to update",
                },
                "name": {
                    "type": "string",
                    "description": "New channel name (optional)",
                },
                "description": {
                    "type": "string",
                    "description": "New channel description (optional)",
                },
                "password": {
                    "type": "string",
                    "description": "New channel password (optional, empty string to remove)",
                },
                "max_clients": {
                    "type": "integer",
                    "description": "Maximum number of clients (optional)",
                },
                "talk_power": {
                    "type": "integer",
                    "description": "Required talk power to speak in channel (optional)",
                },
                "codec_quality": {
                    "type": "integer",
                    "description": "Audio codec quality 1-10 (optional)",
                },
                "permanent": {
                    "type": "boolean",
                    "description": "Make channel permanent (optional)",
                },
            },
            "required": ["channel_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="set_channel_talk_power",
        description="Set talk power requirement for a channel (useful for AFK/silent channels)",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to configure",
                },
                "talk_power": {
                    "type": "integer",
                    "description": "Required talk power (0=everyone can talk, 999=silent channel)",
                },
                "preset": {
                    "type": "string",
                    "description": "Quick preset: 'silent' (999), 'moderated' (50), 'normal' (0)",
                    "enum": ["silent", "moderated", "normal"],
                },
            },
            "required": ["channel_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="channel_info",
        description="Get detailed information about a specific channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to get info for",
                },
            },
            "required": ["channel_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="manage_channel_permissions",
        description="Add or remove specific permissions for a channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to modify permissions for",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add", "remove", "list"],
                },
                "permission": {
                    "type": "string",
                    "description": "Permission name (required for add/remove actions)",
                },
                "value": {
                    "type": "integer",
                    "description": "Permission value (required for add action)",
                },
            },
            "required": ["channel_id", "action"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="client_info_detailed",
        description="Get detailed information about a specific client",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID to get detailed info for",
                },
            },
            "required": ["client_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="update_server_settings",
        description="Update virtual server settings (name, welcome message, max clients, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Server name (optional)",
                },
                "welcome_message": {
                    "type": "string",
                    "description": "Server welcome message (optional)",
                },
                "max_clients": {
                    "type": "integer",
                    "description": "Maximum number of clients (optional)",
                },
                "password": {
                    "type": "string",
                    "description": "Server password (optional, empty string to remove)",
                },
                "hostmessage": {
                    "type": "string",
                    "description": "Host message displayed in server info (optional)",
                },
                "hostmessage_mode": {
                    "type": "integer",
                    "description": "Host message mode: 0=none, 1=log, 2=modal, 3=modalquit (optional)",
                },
                "default_server_group": {
                    "type": "integer",
                    "description": "Default server group ID for new clients (optional)",
                },
                "default_channel_group": {
                    "type": "integer", 
                    "description": "Default channel group ID for new clients (optional)",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="manage_user_permissions",
        description="Manage user permissions: add/remove server groups, set individual permissions",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID to manage permissions for",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add_group", "remove_group", "list_groups", "add_permission", "remove_permission", "list_permissions"],
                },
                "group_id": {
                    "type": "integer",
                    "description": "Server group ID (required for add_group/remove_group actions)",
                },
                "permission": {
                    "type": "string",
                    "description": "Permission name (required for add_permission/remove_permission actions)",
                },
                "value": {
                    "type": "integer",
                    "description": "Permission value (required for add_permission action)",
                },
                "skip": {
                    "type": "boolean",
                    "description": "Skip flag for permission (optional, default: false)",
                    "default": False,
                },
                "negate": {
                    "type": "boolean",
                    "description": "Negate flag for permission (optional, default: false)",
                    "default": False,
                },
            },
            "required": ["client_id", "action"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="diagnose_permissions",
        description="Diagnose current connection permissions and provide troubleshooting help",
        inputSchema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    ),
]

class TeamSpeakMCPServer:
    """TeamSpeak MCP Server class for backward compatibility with tests."""
    
    def __init__(self):
        self.tools = TOOLS
    
    async def handle_list_tools(self, request) -> ListToolsResult:
        """Handle list tools request."""
        return ListToolsResult(tools=self.tools)

async def run_server():
    """Run the MCP server."""
    global ts_connection
    
    # Parse command line arguments
    args = parse_args()
    
    # Initialize connection with CLI arguments
    ts_connection = TeamSpeakConnection(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        server_id=args.server_id
    )
    
    # Create server instance
    server = Server("teamspeak-mcp")
    
    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """Return list of available tools."""
        return TOOLS
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute a requested tool."""
        try:
            if name == "connect_to_server":
                return await _connect_to_server()
            elif name == "send_channel_message":
                return await _send_channel_message(arguments)
            elif name == "send_private_message":
                return await _send_private_message(arguments)
            elif name == "poke_client":
                return await _poke_client(arguments)
            elif name == "list_clients":
                return await _list_clients()
            elif name == "list_channels":
                return await _list_channels()
            elif name == "create_channel":
                return await _create_channel(arguments)
            elif name == "delete_channel":
                return await _delete_channel(arguments)
            elif name == "move_client":
                return await _move_client(arguments)
            elif name == "kick_client":
                return await _kick_client(arguments)
            elif name == "ban_client":
                return await _ban_client(arguments)
            elif name == "server_info":
                return await _server_info()
            elif name == "update_channel":
                return await _update_channel(arguments)
            elif name == "set_channel_talk_power":
                return await _set_channel_talk_power(arguments)
            elif name == "channel_info":
                return await _channel_info(arguments)
            elif name == "manage_channel_permissions":
                return await _manage_channel_permissions(arguments)
            elif name == "client_info_detailed":
                return await _client_info_detailed(arguments)
            elif name == "update_server_settings":
                return await _update_server_settings(arguments)
            elif name == "manage_user_permissions":
                return await _manage_user_permissions(arguments)
            elif name == "diagnose_permissions":
                return await _diagnose_permissions()
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            raise Exception(f"Error: {str(e)}")
    
    logger.info("🚀 Starting TeamSpeak MCP server...")
    logger.info(f"Host: {ts_connection.host}:{ts_connection.port}")
    logger.info(f"User: {ts_connection.user}")
    logger.info(f"Server ID: {ts_connection.server_id}")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="teamspeak",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        if ts_connection:
            await ts_connection.disconnect()

async def _connect_to_server() -> list[TextContent]:
    """Connect to TeamSpeak server."""
    success = await ts_connection.connect()
    if success:
        return [TextContent(type="text", text="✅ TeamSpeak server connection successful")]
    else:
        raise Exception("TeamSpeak server connection failed")

async def _send_channel_message(args: dict) -> list[TextContent]:
    """Send message to a channel."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    message = args["message"]
    channel_id = args.get("channel_id")
    
    try:
        if channel_id:
            await asyncio.to_thread(
                ts_connection.connection.sendtextmessage,
                targetmode=2, target=channel_id, msg=message
            )
        else:
            await asyncio.to_thread(
                ts_connection.connection.sendtextmessage,
                targetmode=2, target=0, msg=message
            )
        
        return [TextContent(type="text", text=f"✅ Message sent to channel: {message}")]
    except Exception as e:
        raise Exception(f"Error sending message: {e}")

async def _send_private_message(args: dict) -> list[TextContent]:
    """Send private message."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    message = args["message"]
    
    try:
        await asyncio.to_thread(
            ts_connection.connection.sendtextmessage,
            targetmode=1, target=client_id, msg=message
        )
        
        return [TextContent(type="text", text=f"✅ Private message sent to client {client_id}: {message}")]
    except Exception as e:
        raise Exception(f"Error sending private message: {e}")

async def _poke_client(args: dict) -> list[TextContent]:
    """Send a poke (alert notification) to a client."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    message = args["message"]
    
    try:
        await asyncio.to_thread(
            ts_connection.connection.clientpoke,
            clid=client_id, msg=message
        )
        
        return [TextContent(type="text", text=f"👉 Poke sent to client {client_id}: {message}")]
    except Exception as e:
        raise Exception(f"Error sending poke: {e}")

async def _list_clients() -> list[TextContent]:
    """List connected clients."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    try:
        clients = await asyncio.to_thread(ts_connection.connection.clientlist)
        
        result = "👥 **Connected clients:**\n\n"
        for client in clients:
            result += f"• **ID {client.get('clid')}**: {client.get('client_nickname')} "
            result += f"(Channel: {client.get('cid')})\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_message = str(e)
        
        # Check for specific permission errors
        if "error id 2568" in error_message or "insufficient client permissions" in error_message:
            diagnostic_result = "❌ **Erreur de permissions insuffisantes**\n\n"
            diagnostic_result += "La commande `list_clients` nécessite des permissions élevées.\n\n"
            diagnostic_result += "**🔧 Solutions possibles :**\n\n"
            diagnostic_result += "1. **Vérifiez votre mot de passe :**\n"
            diagnostic_result += "   - Utilisez un mot de passe ServerQuery valide\n"
            diagnostic_result += "   - Ou utilisez un token admin (commençant par 'token=')\n\n"
            diagnostic_result += "2. **Créez un utilisateur ServerQuery :**\n"
            diagnostic_result += "   ```\n"
            diagnostic_result += "   # Connectez-vous au ServerQuery\n"
            diagnostic_result += "   serverqueryadd client_login_name=mcp_user client_login_password=votre_mot_de_passe\n"
            diagnostic_result += "   servergroupaddclient sgid=6 cldbid=ID_USER  # Groupe Server Admin\n"
            diagnostic_result += "   ```\n\n"
            diagnostic_result += "3. **Obtenez un token admin :**\n"
            diagnostic_result += "   - Regardez les logs du serveur TS3 au démarrage\n"
            diagnostic_result += "   - Ou utilisez: `tokenadd tokentype=0 tokenid1=6`\n\n"
            diagnostic_result += "4. **Vérifiez la configuration :**\n"
            diagnostic_result += f"   - Host: {ts_connection.host}\n"
            diagnostic_result += f"   - User: {ts_connection.user}\n"
            diagnostic_result += f"   - Password: {'[SET]' if ts_connection.password else '[NOT SET]'}\n\n"
            diagnostic_result += "**🔍 Test rapide :**\n"
            diagnostic_result += "Essayez d'abord avec `server_info` qui nécessite moins de permissions."
            
            return [TextContent(type="text", text=diagnostic_result)]
        else:
            raise Exception(f"Error retrieving clients: {e}")

async def _list_channels() -> list[TextContent]:
    """List channels."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    try:
        channels = await asyncio.to_thread(ts_connection.connection.channellist)
        
        result = "📋 **Available channels:**\n\n"
        for channel in channels:
            result += f"• **ID {channel.get('cid')}**: {channel.get('channel_name')}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving channels: {e}")

async def _create_channel(args: dict) -> list[TextContent]:
    """Create a new channel."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    name = args["name"]
    parent_id = args.get("parent_id", 0)
    permanent = args.get("permanent", False)
    
    try:
        channel_type = 1 if permanent else 0
        result = await asyncio.to_thread(
            ts_connection.connection.channelcreate,
            channel_name=name,
            channel_flag_permanent=permanent,
            cpid=parent_id
        )
        
        return [TextContent(type="text", text=f"✅ Channel '{name}' created successfully")]
    except Exception as e:
        raise Exception(f"Error creating channel: {e}")

async def _delete_channel(args: dict) -> list[TextContent]:
    """Delete a channel."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    channel_id = args["channel_id"]
    force = args.get("force", False)
    
    try:
        await asyncio.to_thread(
            ts_connection.connection.channeldelete,
            cid=channel_id, force=1 if force else 0
        )
        
        return [TextContent(type="text", text=f"✅ Channel {channel_id} deleted successfully")]
    except Exception as e:
        raise Exception(f"Error deleting channel: {e}")

async def _move_client(args: dict) -> list[TextContent]:
    """Move a client."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    channel_id = args["channel_id"]
    
    try:
        await asyncio.to_thread(
            ts_connection.connection.clientmove,
            clid=client_id, cid=channel_id
        )
        
        return [TextContent(type="text", text=f"✅ Client {client_id} moved to channel {channel_id}")]
    except Exception as e:
        raise Exception(f"Error moving client: {e}")

async def _kick_client(args: dict) -> list[TextContent]:
    """Kick a client."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    reason = args.get("reason", "Expelled by AI")
    from_server = args.get("from_server", False)
    
    try:
        kick_type = 5 if from_server else 4  # 5 = server, 4 = channel
        await asyncio.to_thread(
            ts_connection.connection.clientkick,
            clid=client_id, reasonid=kick_type, reasonmsg=reason
        )
        
        location = "from server" if from_server else "from channel"
        return [TextContent(type="text", text=f"✅ Client {client_id} kicked {location}: {reason}")]
    except Exception as e:
        raise Exception(f"Error kicking client: {e}")

async def _ban_client(args: dict) -> list[TextContent]:
    """Ban a client."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    reason = args.get("reason", "Banned by AI")
    duration = args.get("duration", 0)
    
    try:
        await asyncio.to_thread(
            ts_connection.connection.banclient,
            clid=client_id, time=duration, banreason=reason
        )
        
        duration_text = "permanently" if duration == 0 else f"for {duration} seconds"
        return [TextContent(type="text", text=f"✅ Client {client_id} banned {duration_text}: {reason}")]
    except Exception as e:
        raise Exception(f"Error banning client: {e}")

async def _server_info() -> list[TextContent]:
    """Get server information."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    try:
        info = await asyncio.to_thread(ts_connection.connection.serverinfo)
        
        result = "🖥️ **TeamSpeak Server Information:**\n\n"
        result += f"• **Name**: {info.get('virtualserver_name', 'N/A')}\n"
        result += f"• **Version**: {info.get('virtualserver_version', 'N/A')}\n"
        result += f"• **Platform**: {info.get('virtualserver_platform', 'N/A')}\n"
        result += f"• **Clients**: {info.get('virtualserver_clientsonline', 'N/A')}/{info.get('virtualserver_maxclients', 'N/A')}\n"
        result += f"• **Uptime**: {info.get('virtualserver_uptime', 'N/A')} seconds\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving server info: {e}")

async def _update_channel(args: dict) -> list[TextContent]:
    """Update channel properties."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    channel_id = args["channel_id"]
    
    # Build kwargs dict with only non-None values
    kwargs = {"cid": channel_id}
    
    if args.get("name"):
        kwargs["channel_name"] = args["name"]
    if args.get("description"):
        kwargs["channel_description"] = args["description"]  
    if args.get("password") is not None:
        kwargs["channel_password"] = args["password"]
    if args.get("max_clients"):
        kwargs["channel_maxclients"] = args["max_clients"]
    if args.get("talk_power") is not None:
        kwargs["channel_needed_talk_power"] = args["talk_power"]
    if args.get("codec_quality"):
        kwargs["channel_codec_quality"] = args["codec_quality"]
    if args.get("permanent") is not None:
        kwargs["channel_flag_permanent"] = 1 if args["permanent"] else 0
    
    try:
        await asyncio.to_thread(ts_connection.connection.channeledit, **kwargs)
        
        changes = [k.replace("channel_", "") for k in kwargs.keys() if k != "cid"]
        result = f"✅ Channel {channel_id} updated successfully\n"
        result += f"📝 Modified properties: {', '.join(changes)}"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error updating channel: {e}")

async def _set_channel_talk_power(args: dict) -> list[TextContent]:
    """Set talk power requirement for a channel."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    channel_id = args["channel_id"]
    talk_power = args.get("talk_power")
    preset = args.get("preset")
    
    # Handle presets
    if preset:
        if preset == "silent":
            talk_power = 999
        elif preset == "moderated":
            talk_power = 50
        elif preset == "normal":
            talk_power = 0
    
    if talk_power is None:
        raise Exception("Either talk_power or preset must be specified")
    
    try:
        await asyncio.to_thread(
            ts_connection.connection.channeledit,
            cid=channel_id,
            channel_needed_talk_power=talk_power
        )
        
        preset_text = f" (preset: {preset})" if preset else ""
        result = f"✅ Talk power for channel {channel_id} set to {talk_power}{preset_text}\n"
        
        if talk_power == 0:
            result += "🔊 Channel is now open - everyone can talk"
        elif talk_power >= 999:
            result += "🔇 Channel is now silent - only high-privilege users can talk"
        elif talk_power >= 50:
            result += "🔒 Channel is now moderated - only moderators+ can talk"
        else:
            result += f"⚡ Custom talk power requirement: {talk_power}"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error setting channel talk power: {e}")

async def _channel_info(args: dict) -> list[TextContent]:
    """Get detailed information about a specific channel."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    channel_id = args["channel_id"]
    
    try:
        response = await asyncio.to_thread(ts_connection.connection.channelinfo, cid=channel_id)
        
        # Handle TS3QueryResponse object - try different access methods
        if hasattr(response, 'data') and response.data:
            # If response has .data attribute (list of dicts)
            info = response.data[0] if response.data else {}
        elif hasattr(response, '__iter__') and not isinstance(response, str):
            # If response is iterable (list of dicts)
            info = list(response)[0] if response else {}
        else:
            # If response is directly a dict-like object
            info = response
        
        # Helper function to safely get values
        def safe_get(key, default='N/A'):
            if hasattr(info, 'get'):
                return info.get(key, default)
            elif hasattr(info, key):
                return getattr(info, key, default)
            else:
                return default
        
        result = "📋 **Channel Information:**\n\n"
        result += f"• **ID**: {safe_get('cid')}\n"
        result += f"• **Name**: {safe_get('channel_name')}\n"
        result += f"• **Description**: {safe_get('channel_description')}\n"
        result += f"• **Topic**: {safe_get('channel_topic')}\n"
        result += f"• **Password Protected**: {'Yes' if safe_get('channel_flag_password') == '1' else 'No'}\n"
        result += f"• **Max Clients**: {safe_get('channel_maxclients', 'Unlimited')}\n"
        result += f"• **Current Clients**: {safe_get('total_clients', '0')}\n"
        result += f"• **Talk Power Required**: {safe_get('channel_needed_talk_power', '0')}\n"
        result += f"• **Codec**: {safe_get('channel_codec')}\n"
        result += f"• **Codec Quality**: {safe_get('channel_codec_quality')}\n"
        result += f"• **Type**: {'Permanent' if safe_get('channel_flag_permanent') == '1' else 'Temporary'}\n"
        result += f"• **Order**: {safe_get('channel_order')}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving channel info: {e}")

async def _manage_channel_permissions(args: dict) -> list[TextContent]:
    """Add or remove specific permissions for a channel."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    channel_id = args["channel_id"]
    action = args["action"]
    permission = args.get("permission")
    value = args.get("value")
    
    try:
        if action == "add":
            if not permission or value is None:
                raise ValueError("Permission name and value required for add action")
            
            await asyncio.to_thread(
                ts_connection.connection.channeladdperm,
                cid=channel_id, permsid=permission, permvalue=value
            )
            result = f"✅ Permission '{permission}' added to channel {channel_id} with value {value}"
            
        elif action == "remove":
            if not permission:
                raise ValueError("Permission name required for remove action")
            
            await asyncio.to_thread(
                ts_connection.connection.channeldelperm,
                cid=channel_id, permsid=permission
            )
            result = f"✅ Permission '{permission}' removed from channel {channel_id}"
            
        elif action == "list":
            perms = await asyncio.to_thread(
                ts_connection.connection.channelpermlist,
                cid=channel_id, permsid=True
            )
            
            result = f"📋 **Channel {channel_id} Permissions:**\n\n"
            if perms:
                for perm in perms:
                    perm_name = perm.get('permsid', 'N/A')
                    perm_value = perm.get('permvalue', 'N/A')
                    result += f"• **{perm_name}**: {perm_value}\n"
            else:
                result += "No custom permissions set for this channel."
                
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing channel permissions: {e}")

async def _client_info_detailed(args: dict) -> list[TextContent]:
    """Get detailed information about a specific client."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    
    try:
        response = await asyncio.to_thread(ts_connection.connection.clientinfo, clid=client_id)
        
        # Handle TS3QueryResponse object - try different access methods
        if hasattr(response, 'data') and response.data:
            # If response has .data attribute (list of dicts)
            info = response.data[0] if response.data else {}
        elif hasattr(response, '__iter__') and not isinstance(response, str):
            # If response is iterable (list of dicts)
            info = list(response)[0] if response else {}
        else:
            # If response is directly a dict-like object
            info = response
        
        # Helper function to safely get values
        def safe_get(key, default='N/A'):
            if hasattr(info, 'get'):
                return info.get(key, default)
            elif hasattr(info, key):
                return getattr(info, key, default)
            else:
                return default
        
        result = "👤 **Client Information:**\n\n"
        result += f"• **ID**: {safe_get('clid')}\n"
        result += f"• **Database ID**: {safe_get('client_database_id')}\n"
        result += f"• **Nickname**: {safe_get('client_nickname')}\n"
        
        unique_id = safe_get('client_unique_identifier')
        if unique_id and unique_id != 'N/A' and len(unique_id) > 32:
            unique_id = unique_id[:32] + "..."
        result += f"• **Unique ID**: {unique_id}\n"
        
        result += f"• **Channel ID**: {safe_get('cid')}\n"
        result += f"• **Talk Power**: {safe_get('client_talk_power', '0')}\n"
        result += f"• **Client Type**: {'ServerQuery' if safe_get('client_type') == '1' else 'Regular'}\n"
        result += f"• **Platform**: {safe_get('client_platform')}\n"
        result += f"• **Version**: {safe_get('client_version')}\n"
        result += f"• **Away**: {'Yes' if safe_get('client_away') == '1' else 'No'}\n"
        result += f"• **Away Message**: {safe_get('client_away_message')}\n"
        result += f"• **Input Muted**: {'Yes' if safe_get('client_input_muted') == '1' else 'No'}\n"
        result += f"• **Output Muted**: {'Yes' if safe_get('client_output_muted') == '1' else 'No'}\n"
        result += f"• **Connected Since**: {safe_get('client_created')}\n"
        result += f"• **Last Connected**: {safe_get('client_lastconnected')}\n"
        result += f"• **Connection Time**: {safe_get('connection_connected_time')}ms\n"
        result += f"• **Country**: {safe_get('client_country')}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving client info: {e}")

async def _update_server_settings(args: dict) -> list[TextContent]:
    """Update virtual server settings."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    name = args.get("name")
    welcome_message = args.get("welcome_message")
    max_clients = args.get("max_clients")
    password = args.get("password")
    hostmessage = args.get("hostmessage")
    hostmessage_mode = args.get("hostmessage_mode")
    default_server_group = args.get("default_server_group")
    default_channel_group = args.get("default_channel_group")
    
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
            kwargs["virtualserver_hostmessage_mode"] = hostmessage_mode
        if default_server_group:
            kwargs["virtualserver_default_server_group"] = default_server_group
        if default_channel_group:
            kwargs["virtualserver_default_channel_group"] = default_channel_group
        
        await asyncio.to_thread(ts_connection.connection.serveredit, **kwargs)
        
        changes = [k for k, v in kwargs.items() if v is not None]
        result = f"✅ Server settings updated successfully\n"
        result += f"📝 Modified properties: {', '.join(changes)}"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error updating server settings: {e}")

async def _manage_user_permissions(args: dict) -> list[TextContent]:
    """Manage user permissions."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    client_id = args["client_id"]
    action = args["action"]
    group_id = args.get("group_id")
    permission = args.get("permission")
    value = args.get("value")
    skip = args.get("skip", False)
    negate = args.get("negate", False)
    
    try:
        # First, get client database ID for some operations
        client_info = None
        if action in ["list_groups", "add_permission", "remove_permission", "list_permissions"]:
            client_info = await asyncio.to_thread(ts_connection.connection.clientinfo, clid=client_id)
            # Handle response format
            if hasattr(client_info, 'data') and client_info.data:
                client_info = client_info.data[0]
            elif hasattr(client_info, '__iter__') and not isinstance(client_info, str):
                client_info = list(client_info)[0] if client_info else {}
        
        if action == "add_group":
            if not group_id:
                raise ValueError("Server group ID required for add_group action")
            
            await asyncio.to_thread(
                ts_connection.connection.servergroupaddclient,
                sgid=group_id, clid=client_id
            )
            result = f"✅ Client {client_id} added to server group {group_id}"
            
        elif action == "remove_group":
            if not group_id:
                raise ValueError("Server group ID required for remove_group action")
            
            await asyncio.to_thread(
                ts_connection.connection.servergroupdelclient,
                sgid=group_id, clid=client_id
            )
            result = f"✅ Client {client_id} removed from server group {group_id}"
            
        elif action == "list_groups":
            # Use the client database ID to get server groups
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            groups = await asyncio.to_thread(
                ts_connection.connection.servergroupsbyclientid,
                cldbid=client_database_id
            )
            
            result = f"📋 **Client {client_id} Server Groups:**\n\n"
            if groups:
                for group in groups:
                    group_name = group.get('name', 'N/A')
                    group_id = group.get('sgid', 'N/A')
                    result += f"• **{group_name}** (ID: {group_id})\n"
            else:
                result += "No server groups assigned to this client."
                
        elif action == "add_permission":
            if not permission or value is None:
                raise ValueError("Permission name and value required for add_permission action")
            
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            await asyncio.to_thread(
                ts_connection.connection.clientaddperm,
                cldbid=client_database_id, permsid=permission, permvalue=value, skip=skip, negate=negate
            )
            result = f"✅ Permission '{permission}' added to client {client_id} with value {value}"
            
        elif action == "remove_permission":
            if not permission:
                raise ValueError("Permission name required for remove_permission action")
            
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            await asyncio.to_thread(
                ts_connection.connection.clientdelperm,
                cldbid=client_database_id, permsid=permission
            )
            result = f"✅ Permission '{permission}' removed from client {client_id}"
            
        elif action == "list_permissions":
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            perms = await asyncio.to_thread(
                ts_connection.connection.clientpermlist,
                cldbid=client_database_id, permsid=True
            )
            
            result = f"📋 **Client {client_id} Permissions:**\n\n"
            if perms:
                for perm in perms:
                    perm_name = perm.get('permsid', 'N/A')
                    perm_value = perm.get('permvalue', 'N/A')
                    result += f"• **{perm_name}**: {perm_value}\n"
            else:
                result += "No custom permissions assigned to this client."
                
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing user permissions: {e}")

async def _diagnose_permissions() -> list[TextContent]:
    """Diagnose current connection permissions and provide troubleshooting help."""
    if not ts_connection.is_connected():
        raise Exception("Not connected to TeamSpeak server")
    
    result = "🔍 **Diagnostic des Permissions TeamSpeak MCP**\n\n"
    
    # Test 1: Basic whoami
    try:
        whoami_response = await asyncio.to_thread(ts_connection.connection.whoami)
        
        # Handle TS3QueryResponse object - try different access methods
        if hasattr(whoami_response, 'data') and whoami_response.data:
            whoami = whoami_response.data[0] if whoami_response.data else {}
        elif hasattr(whoami_response, '__iter__') and not isinstance(whoami_response, str):
            whoami = list(whoami_response)[0] if whoami_response else {}
        else:
            whoami = whoami_response
            
        # Helper function to safely get values
        def safe_get(obj, key, default='N/A'):
            if hasattr(obj, 'get'):
                return obj.get(key, default)
            elif hasattr(obj, key):
                return getattr(obj, key, default)
            else:
                return default
        
        result += "✅ **Connexion de base** : OK\n"
        result += f"   - Client ID: {safe_get(whoami, 'client_id')}\n"
        result += f"   - Database ID: {safe_get(whoami, 'client_database_id')}\n"
        result += f"   - Nickname: {safe_get(whoami, 'client_nickname')}\n"
        result += f"   - Type: {'ServerQuery' if safe_get(whoami, 'client_type') == '1' else 'Regular'}\n\n"
        
        # Store client_database_id for later use
        client_db_id = safe_get(whoami, 'client_database_id')
        
    except Exception as e:
        result += f"❌ **Connexion de base** : ÉCHEC\n   Erreur: {e}\n\n"
        return [TextContent(type="text", text=result)]
    
    # Test 2: Server info (basic permission)
    try:
        await asyncio.to_thread(ts_connection.connection.serverinfo)
        result += "✅ **server_info** : OK (permissions de base)\n"
    except Exception as e:
        result += f"❌ **server_info** : ÉCHEC - {e}\n"
    
    # Test 3: Client list (elevated permission)
    try:
        await asyncio.to_thread(ts_connection.connection.clientlist)
        result += "✅ **list_clients** : OK (permissions élevées)\n"
    except Exception as e:
        result += f"❌ **list_clients** : ÉCHEC - {e}\n"
    
    # Test 4: Channel list
    try:
        await asyncio.to_thread(ts_connection.connection.channellist)
        result += "✅ **list_channels** : OK\n"
    except Exception as e:
        result += f"❌ **list_channels** : ÉCHEC - {e}\n"
    
    # Test 5: Try to get current permissions
    try:
        if client_db_id and client_db_id != 'N/A':
            # Try to get server groups
            try:
                groups_response = await asyncio.to_thread(ts_connection.connection.servergroupsbyclientid, cldbid=client_db_id)
                
                # Handle response format
                if hasattr(groups_response, 'data') and groups_response.data:
                    groups = groups_response.data
                elif hasattr(groups_response, '__iter__') and not isinstance(groups_response, str):
                    groups = list(groups_response)
                else:
                    groups = [groups_response] if groups_response else []
                
                result += f"✅ **Groupes serveur** : OK\n"
                for group in groups[:3]:  # Limit to first 3 groups
                    group_name = safe_get(group, 'name', 'N/A')
                    group_id = safe_get(group, 'sgid', 'N/A')
                    result += f"   - {group_name} (ID: {group_id})\n"
                    
            except Exception as e:
                result += f"❌ **Groupes serveur** : ÉCHEC - {e}\n"
        else:
            result += f"⚠️ **Groupes serveur** : Impossible (pas de client_database_id)\n"
            
    except Exception as e:
        result += f"❌ **Analyse des permissions** : ÉCHEC - {e}\n"
    
    result += "\n**📊 Configuration actuelle :**\n"
    result += f"   - Host: {ts_connection.host}:{ts_connection.port}\n"
    result += f"   - User: {ts_connection.user}\n"
    result += f"   - Password: {'✅ Fourni' if ts_connection.password else '❌ Non fourni'}\n"
    result += f"   - Server ID: {ts_connection.server_id}\n\n"
    
    result += "**💡 Recommandations :**\n\n"
    result += "Si vous avez des échecs :\n"
    result += "1. **Vérifiez votre mot de passe ServerQuery**\n"
    result += "2. **Utilisez un token admin** si disponible\n"
    result += "3. **Créez un utilisateur ServerQuery avec permissions admin**\n"
    result += "4. **Vérifiez que le port 10011 (ServerQuery) est accessible**\n\n"
    result += "Pour plus d'aide, utilisez la commande `list_clients` qui fournit un diagnostic détaillé en cas d'erreur."
    
    return [TextContent(type="text", text=result)]

def main():
    """Entry point for setuptools."""
    asyncio.run(run_server())

if __name__ == "__main__":
    main() 