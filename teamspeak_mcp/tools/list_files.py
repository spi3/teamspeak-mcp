import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_list_files_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def list_files(
        channel_id: int, path: str = "/", channel_password: Optional[str] = None
    ) -> str:
        """
        List files in a channel's file repository
        Args:
            - channel_id: Channel ID to list files for
            - path: Directory path to list (default: root '/')
            - channel_password: Channel password if required (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.ftgetfilelist(
                cid=channel_id,
                path=path,
                cpw=channel_password if channel_password else "",
            )

            # Extract files list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                files = response.parsed
            else:
                # Fallback to container emulation
                files = list(response)

            result = f"📁 **Files in Channel {channel_id} (Path: {path}):**\n\n"
            if not files:
                result += "No files found in this directory."
            else:
                for file in files:
                    file_name = file.get("name", "N/A")
                    file_size = file.get("size", "N/A")
                    file_type = "Directory" if file.get("type") == "0" else "File"
                    result += f"• **{file_name}** ({file_type})\n"
                    if file_type == "File":
                        result += f"  - Size: {file_size} bytes\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving files: {e}")
