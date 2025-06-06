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
            await asyncio.to_thread(self.connection.login, client_login_name=self.user, client_login_password=self.password)
            await asyncio.to_thread(self.connection.use, sid=self.server_id)
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
]

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
                        notification_options=None,
                        experimental_capabilities=None,
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

def main():
    """Entry point for setuptools."""
    asyncio.run(run_server())

if __name__ == "__main__":
    main() 