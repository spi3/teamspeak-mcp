import argparse
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

logger = logging.getLogger(__name__)


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

    def connect(self) -> bool:
        """Connect to TeamSpeak server."""
        try:
            # Use asyncio.to_thread for blocking operations
            self.connection = ts3.query.TS3Connection(self.host, self.port)
            self.connection.use(sid=self.server_id)

            # Authenticate if password is provided
            if self.password:
                # First try to login with username/password (classic ServerQuery auth)
                try:
                    self.connection.login(
                        client_login_name=self.user, client_login_password=self.password
                    )
                    logger.info("Successfully authenticated with username/password")
                except Exception as login_error:
                    logger.info(
                        f"Username/password authentication failed: {login_error}"
                    )

                    # If login fails, try to use as admin token
                    try:
                        self.connection.tokenuse(token=self.password)
                        logger.info("Successfully used admin privilege key")
                    except Exception as token_error:
                        logger.warning(
                            f"Could not use admin token either: {token_error}"
                        )
                        logger.warning("Continuing with basic anonymous permissions")
            else:
                logger.info("No password provided, using anonymous connection")

            # Test basic connectivity and permissions
            try:
                # Try a simple command to verify permissions
                self.connection.whoami()
                logger.info("Basic connectivity test passed")
            except Exception as test_error:
                logger.warning(f"Basic connectivity test failed: {test_error}")

            logger.info("TeamSpeak connection established successfully")
            return True
        except Exception as e:
            logger.error(f"TeamSpeak connection error: {e}")
            self.connection = None
            return False

    def disconnect(self):
        """Disconnect from TeamSpeak server."""
        if self.connection:
            try:
                self.connection.quit()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connection = None
                logger.info("TeamSpeak disconnected")

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connection is not None
