"""
TeamSpeak MCP Server - Allows controlling TeamSpeak from AI models.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
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
from mcp.server.fastmcp import FastMCP

from teamspeak_mcp.tools import register_all_tools

# Logging configuration - ensure all logs go to stderr for MCP protocol compliance
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TeamSpeak MCP Server")
    parser.add_argument(
        "--host",
        default=os.getenv("TEAMSPEAK_HOST", "localhost"),
        help="TeamSpeak server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("TEAMSPEAK_PORT", "10011")),
        help="TeamSpeak ServerQuery port",
    )
    parser.add_argument(
        "--user",
        default=os.getenv("TEAMSPEAK_USER", "serveradmin"),
        help="TeamSpeak ServerQuery username",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("TEAMSPEAK_PASSWORD", ""),
        help="TeamSpeak ServerQuery password",
    )
    parser.add_argument(
        "--server-id",
        type=int,
        default=int(os.getenv("TEAMSPEAK_SERVER_ID", "1")),
        help="TeamSpeak virtual server ID",
    )
    parser.add_argument(
        "--mcp-mode",
        choices=["stdio", "streamable-http"],
        default=os.getenv("MCP_MODE", "stdio"),
        help="MCP server mode",
    )
    return parser.parse_args()


def run_server():
    """Run the MCP server."""
    ts_connection = None

    # Parse command line arguments
    args = parse_args()

    # Initialize connection with CLI arguments
    ts_connection = TeamSpeakConnection(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        server_id=args.server_id,
    ).connect()

    # Create server instance
    mcp = FastMCP("teamspeak-mcp")

    register_all_tools(mcp, ts_connection)

    logger.info("🚀 Starting TeamSpeak MCP server...")
    logger.info(f"Host: {ts_connection.host}:{ts_connection.port}")
    logger.info(f"User: {ts_connection.user}")
    logger.info(f"Server ID: {ts_connection.server_id}")

    try:
        if args.mcp_mode == "stdio":
            mcp.run(transport="stdio")
        elif args.mcp_mode == "streamable-http":
            mcp.run(transport="streamable-http")
    finally:
        if ts_connection:
            ts_connection.disconnect()


def main():
    """Entry point for setuptools."""
    run_server()


if __name__ == "__main__":
    main()
