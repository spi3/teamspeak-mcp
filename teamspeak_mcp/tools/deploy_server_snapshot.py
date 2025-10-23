import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_deploy_server_snapshot_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def deploy_server_snapshot(snapshot_data: str) -> str:
        """
        Deploy/restore a server configuration from a snapshot
        Args:
            - snapshot_data: Snapshot data to deploy (from create_server_snapshot)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            ts_connection.connection.serversnapshotdeploy(
                virtualserver_snapshot=snapshot_data,
            )
            result = "✅ Server snapshot deployed successfully\n\n"
            result += "⚠️ **Note**: The server configuration has been restored from the snapshot."

            return result
        except Exception as e:
            raise Exception(f"Error deploying server snapshot: {e}")
