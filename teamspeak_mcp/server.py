"""
TeamSpeak MCP Server - Allows controlling TeamSpeak from AI models.
"""

import asyncio
import logging
import os
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

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamSpeakConnection:
    """TeamSpeak connection manager."""
    
    def __init__(self):
        self.connection: Optional[ts3.query.TS3Connection] = None
        self.host = os.getenv("TEAMSPEAK_HOST", "localhost")
        self.port = int(os.getenv("TEAMSPEAK_PORT", "10011"))
        self.user = os.getenv("TEAMSPEAK_USER", "serveradmin")
        self.password = os.getenv("TEAMSPEAK_PASSWORD", "")
        self.server_id = int(os.getenv("TEAMSPEAK_SERVER_ID", "1"))
        
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

# Global connection instance
ts_connection = TeamSpeakConnection()

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

class TeamSpeakMCPServer:
    """MCP Server for TeamSpeak."""
    
    def __init__(self):
        self.server = Server("teamspeak-mcp")
    
    async def handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Return list of available tools."""
        return ListToolsResult(tools=TOOLS)
    
    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Execute a requested tool."""
        try:
            if request.params.name == "connect_to_server":
                return await self._connect_to_server()
            elif request.params.name == "send_channel_message":
                return await self._send_channel_message(request.params.arguments)
            elif request.params.name == "send_private_message":
                return await self._send_private_message(request.params.arguments)
            elif request.params.name == "list_clients":
                return await self._list_clients()
            elif request.params.name == "list_channels":
                return await self._list_channels()
            elif request.params.name == "create_channel":
                return await self._create_channel(request.params.arguments)
            elif request.params.name == "delete_channel":
                return await self._delete_channel(request.params.arguments)
            elif request.params.name == "move_client":
                return await self._move_client(request.params.arguments)
            elif request.params.name == "kick_client":
                return await self._kick_client(request.params.arguments)
            elif request.params.name == "ban_client":
                return await self._ban_client(request.params.arguments)
            elif request.params.name == "server_info":
                return await self._server_info()
            else:
                raise ValueError(f"Unknown tool: {request.params.name}")
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
    
    async def _connect_to_server(self) -> CallToolResult:
        """Connect to TeamSpeak server."""
        success = await ts_connection.connect()
        if success:
            return CallToolResult(
                content=[TextContent(type="text", text="✅ TeamSpeak server connection successful")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="❌ TeamSpeak server connection failed")],
                isError=True
            )
    
    async def _send_channel_message(self, args: dict) -> CallToolResult:
        """Send message to a channel."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
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
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Message sent to channel: {message}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error sending message: {e}")],
                isError=True
            )
    
    async def _send_private_message(self, args: dict) -> CallToolResult:
        """Send private message."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        client_id = args["client_id"]
        message = args["message"]
        
        try:
            await asyncio.to_thread(
                ts_connection.connection.sendtextmessage,
                targetmode=1, target=client_id, msg=message
            )
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Private message sent to client {client_id}: {message}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error sending private message: {e}")],
                isError=True
            )
    
    async def _list_clients(self) -> CallToolResult:
        """List connected clients."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        try:
            clients = await asyncio.to_thread(ts_connection.connection.clientlist)
            
            result = "👥 **Connected clients:**\n\n"
            for client in clients:
                result += f"• **ID {client.get('clid')}**: {client.get('client_nickname')} "
                result += f"(Channel: {client.get('cid')})\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error retrieving clients: {e}")],
                isError=True
            )
    
    async def _list_channels(self) -> CallToolResult:
        """List channels."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        try:
            channels = await asyncio.to_thread(ts_connection.connection.channellist)
            
            result = "📋 **Available channels:**\n\n"
            for channel in channels:
                result += f"• **ID {channel.get('cid')}**: {channel.get('channel_name')}\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error retrieving channels: {e}")],
                isError=True
            )
    
    async def _create_channel(self, args: dict) -> CallToolResult:
        """Create a new channel."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
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
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Channel '{name}' created successfully")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error creating channel: {e}")],
                isError=True
            )
    
    async def _delete_channel(self, args: dict) -> CallToolResult:
        """Delete a channel."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        channel_id = args["channel_id"]
        force = args.get("force", False)
        
        try:
            await asyncio.to_thread(
                ts_connection.connection.channeldelete,
                cid=channel_id, force=1 if force else 0
            )
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Channel {channel_id} deleted successfully")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error deleting channel: {e}")],
                isError=True
            )
    
    async def _move_client(self, args: dict) -> CallToolResult:
        """Move a client."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        client_id = args["client_id"]
        channel_id = args["channel_id"]
        
        try:
            await asyncio.to_thread(
                ts_connection.connection.clientmove,
                clid=client_id, cid=channel_id
            )
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Client {client_id} moved to channel {channel_id}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error moving client: {e}")],
                isError=True
            )
    
    async def _kick_client(self, args: dict) -> CallToolResult:
        """Kick a client."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
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
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Client {client_id} kicked {location}: {reason}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error kicking client: {e}")],
                isError=True
            )
    
    async def _ban_client(self, args: dict) -> CallToolResult:
        """Ban a client."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        client_id = args["client_id"]
        reason = args.get("reason", "Banned by AI")
        duration = args.get("duration", 0)
        
        try:
            await asyncio.to_thread(
                ts_connection.connection.banclient,
                clid=client_id, time=duration, banreason=reason
            )
            
            duration_text = "permanently" if duration == 0 else f"for {duration} seconds"
            return CallToolResult(
                content=[TextContent(type="text", text=f"✅ Client {client_id} banned {duration_text}: {reason}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error banning client: {e}")],
                isError=True
            )
    
    async def _server_info(self) -> CallToolResult:
        """Get server information."""
        if not ts_connection.is_connected():
            return CallToolResult(
                content=[TextContent(type="text", text="❌ Not connected to TeamSpeak server")],
                isError=True
            )
        
        try:
            info = await asyncio.to_thread(ts_connection.connection.serverinfo)
            
            result = "🖥️ **TeamSpeak Server Information:**\n\n"
            result += f"• **Name**: {info.get('virtualserver_name', 'N/A')}\n"
            result += f"• **Version**: {info.get('virtualserver_version', 'N/A')}\n"
            result += f"• **Platform**: {info.get('virtualserver_platform', 'N/A')}\n"
            result += f"• **Clients**: {info.get('virtualserver_clientsonline', 'N/A')}/{info.get('virtualserver_maxclients', 'N/A')}\n"
            result += f"• **Uptime**: {info.get('virtualserver_uptime', 'N/A')} seconds\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error retrieving server info: {e}")],
                isError=True
            )

async def main():
    """Main MCP server function."""
    server_instance = TeamSpeakMCPServer()
    
    # Configure handlers
    server_instance.server.list_tools = server_instance.handle_list_tools
    server_instance.server.call_tool = server_instance.handle_call_tool
    
    logger.info("🚀 Starting TeamSpeak MCP server...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="teamspeak",
                    server_version="1.0.0",
                    capabilities=server_instance.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )
    finally:
        await ts_connection.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 