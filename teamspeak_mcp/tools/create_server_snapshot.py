import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_create_server_snapshot_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def create_server_snapshot() -> str:
        """
        Create a snapshot of the virtual server configuration
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.serversnapshotcreate()

            # Extract snapshot data
            if hasattr(response, "parsed") and response.parsed:
                snapshot_data = response.parsed[0]
            else:
                snapshot_data = response[0] if response else {}

            result = "📸 **Server Snapshot Created Successfully**\n\n"
            result += "⚠️ **Important**: Save this snapshot data for restoration:\n\n"

            # The snapshot data is typically very long, so we'll show a preview
            if isinstance(snapshot_data, dict):
                for key, value in snapshot_data.items():
                    if len(str(value)) > 100:
                        preview = str(value)[:100] + "..."
                        result += f"• **{key}**: {preview}\n"
                    else:
                        result += f"• **{key}**: {value}\n"
            else:
                # If it's a string, show preview
                snapshot_str = str(snapshot_data)
                if len(snapshot_str) > 500:
                    result += f"```\n{snapshot_str[:500]}...\n```\n"
                else:
                    result += f"```\n{snapshot_str}\n```\n"

            result += "\n💡 **Tip**: Use `deploy_server_snapshot` to restore this configuration."

            return result
        except Exception as e:
            raise Exception(f"Error creating server snapshot: {e}")
