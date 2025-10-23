#!/usr/bin/env python3
"""
Test script for TeamSpeak MCP server.
Used to test functionality without Claude Desktop.
"""

import asyncio
import json
import os
import sys
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection

# Global connection instance
ts_connection = None


def test_connection():
    """Test TeamSpeak server connection."""
    print("🔍 Testing TeamSpeak server connection...", file=sys.stderr)

    # Check environment variables
    required_vars = ["TEAMSPEAK_HOST", "TEAMSPEAK_USER", "TEAMSPEAK_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(
            f"❌ Missing environment variables: {', '.join(missing_vars)}",
            file=sys.stderr,
        )
        print("💡 Create a .env file based on config.example.env", file=sys.stderr)
        return False

    success = ts_connection.connect()
    if success:
        print("✅ Connection successful!", file=sys.stderr)
        ts_connection.disconnect()
        return True
    else:
        print("❌ Connection failed", file=sys.stderr)
        return False

def main():
    """Main test function."""
    global ts_connection

    print("🚀 TeamSpeak MCP Tests\n", file=sys.stderr)

    # Load environment variables from .env or .env.test if present
    env_files = [".env.test", ".env"]
    loaded_env = False

    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📄 Loading configuration from {env_file}", file=sys.stderr)
            with open(env_file, "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
            loaded_env = True
            break

    if not loaded_env:
        print(
            "⚠️  .env file not found, using system environment variables",
            file=sys.stderr,
        )

    # Initialize TeamSpeak connection
    ts_connection = TeamSpeakConnection()

    # Run tests
    connection_ok = test_connection()

    if connection_ok:
        print("\n✅ All tests passed! TeamSpeak MCP is ready to use.", file=sys.stderr)
        print("\n🎯 Next steps:", file=sys.stderr)
        print("1. Add configuration to Claude Desktop (see README.md)", file=sys.stderr)
        print("2. Restart Claude Desktop", file=sys.stderr)
        print(
            "3. Test with commands like 'Connect to TeamSpeak server'", file=sys.stderr
        )
    else:
        print("\n❌ Some tests failed. Check your configuration.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
