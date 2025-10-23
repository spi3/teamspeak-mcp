import argparse
import logging
import os
import sys
import threading
import time
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
        
        # Connection monitoring attributes
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring_flag = threading.Event()
        self._monitor_interval = 30  # Check every 30 seconds
        self._reconnect_max_attempts = 5
        self._reconnect_delay = 2  # Initial delay in seconds
        self._connection_lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to TeamSpeak server."""
        try:
            with self._connection_lock:
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
            
            # Start monitoring thread after successful connection
            self._start_monitoring_thread()
            return True
        except Exception as e:
            logger.error(f"TeamSpeak connection error: {e}")
            with self._connection_lock:
                self.connection = None
            return False

    def disconnect(self):
        """Disconnect from TeamSpeak server."""
        # Stop monitoring thread first
        self._stop_monitoring_thread()
        
        with self._connection_lock:
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

    def _check_connection_health(self) -> bool:
        """Check if the connection is still active by running a simple query."""
        if self.connection is None:
            return False
        
        try:
            self.connection.whoami()
            return True
        except Exception as e:
            logger.debug(f"Connection health check failed: {e}")
            return False

    def _monitor_connection(self):
        """Monitor connection and attempt to reconnect if needed."""
        reconnect_attempts = 0
        current_delay = self._reconnect_delay
        
        while not self._stop_monitoring_flag.is_set():
            try:
                # Check connection health
                if not self._check_connection_health():
                    logger.warning("Connection lost to TeamSpeak server")
                    reconnect_attempts = 0
                    current_delay = self._reconnect_delay
                    
                    # Attempt to reconnect
                    while reconnect_attempts < self._reconnect_max_attempts:
                        if self._stop_monitoring_flag.is_set():
                            return
                        
                        reconnect_attempts += 1
                        logger.info(
                            f"Attempting to reconnect to TeamSpeak server "
                            f"(attempt {reconnect_attempts}/{self._reconnect_max_attempts})"
                        )
                        
                        # Wait before attempting reconnection
                        if self._stop_monitoring_flag.wait(timeout=current_delay):
                            return  # Monitoring stopped while waiting
                        
                        if self.connect():
                            logger.info("Successfully reconnected to TeamSpeak server")
                            reconnect_attempts = 0
                            current_delay = self._reconnect_delay
                            break
                        else:
                            logger.warning(
                                f"Reconnection attempt {reconnect_attempts} failed"
                            )
                            # Exponential backoff with max cap at 60 seconds
                            current_delay = min(current_delay * 2, 60)
                    else:
                        # Max reconnection attempts reached
                        logger.error(
                            f"Failed to reconnect after {self._reconnect_max_attempts} attempts"
                        )
                        with self._connection_lock:
                            self.connection = None
                
                # Wait before next health check
                if self._stop_monitoring_flag.wait(timeout=self._monitor_interval):
                    return  # Monitoring stopped
                    
            except Exception as e:
                logger.error(f"Error in connection monitoring thread: {e}")
                # Wait a bit before retrying to avoid rapid error loops
                if self._stop_monitoring_flag.wait(timeout=5):
                    return

    def _start_monitoring_thread(self):
        """Start the connection monitoring thread."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitoring_flag.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_connection, daemon=True
            )
            self._monitor_thread.start()
            logger.info("Connection monitoring thread started")

    def _stop_monitoring_thread(self):
        """Stop the connection monitoring thread."""
        if self._monitor_thread is not None:
            self._stop_monitoring_flag.set()
            if self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
            logger.info("Connection monitoring thread stopped")
