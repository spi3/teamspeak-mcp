import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_manage_file_permissions_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def manage_file_permissions(
        action: str, transfer_id: Optional[int] = None, delete_partial: bool = False
    ) -> str:
        """
        List active file transfers and manage file transfer permissions
        Args:
            - action: Action to perform (list_transfers or stop_transfer)
            - transfer_id: File transfer ID (required for stop_transfer action)
            - delete_partial: Delete partial file when stopping transfer (default: false)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if action == "list_transfers":
                response = ts_connection.connection.ftlist()

                # Extract transfers list - response.parsed is a list of dictionaries
                if hasattr(response, "parsed"):
                    transfers = response.parsed
                else:
                    # Fallback to container emulation
                    transfers = list(response)

                result = "📋 **Active File Transfers:**\n\n"
                if not transfers:
                    result += "No active file transfers."
                else:
                    for transfer in transfers:
                        transfer_id_val = transfer.get("serverftfid", "N/A")
                        client_id = transfer.get("clid", "N/A")
                        file_name = transfer.get("name", "N/A")
                        file_size = transfer.get("size", "N/A")
                        status = transfer.get("status", "N/A")
                        result += f"• **Transfer ID {transfer_id_val}**:\n"
                        result += f"  - Client: {client_id}\n"
                        result += f"  - File: {file_name}\n"
                        result += f"  - Size: {file_size} bytes\n"
                        result += f"  - Status: {status}\n\n"
            elif action == "stop_transfer":
                if not transfer_id:
                    raise ValueError("Transfer ID required for stop_transfer action")

                ts_connection.connection.ftstop(
                    serverftfid=transfer_id,
                    delete=1 if delete_partial else 0,
                )
                result = f"✅ File transfer {transfer_id} stopped"
            else:
                raise ValueError(f"Unknown action: {action}")

            return result
        except Exception as e:
            raise Exception(f"Error managing file permissions: {e}")
