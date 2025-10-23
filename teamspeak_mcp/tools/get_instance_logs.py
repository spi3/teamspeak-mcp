import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_get_instance_logs_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def get_instance_logs(
        lines: int = 50, reverse: bool = True, begin_pos: Optional[int] = None
    ) -> str:
        """
        Get instance-level logs instead of virtual server logs
        Args:
            - lines: Number of log lines to retrieve (1-100, default: 50)
            - reverse: Show logs in reverse order (newest first, default: true)
            - begin_pos: Starting position in log file (optional)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            kwargs = {
                "lines": lines,
                "reverse": 1 if reverse else 0,
                "instance": 1,  # This requests instance logs instead of virtual server logs
            }

            if begin_pos is not None:
                kwargs["begin_pos"] = begin_pos

            response = ts_connection.connection.logview(**kwargs)

            result = f"📋 **TeamSpeak Instance Logs (last {lines} entries)**\n\n"

            if hasattr(response, "parsed") and response.parsed:
                log_data = response.parsed[0]
                if "l" in log_data:
                    # Split log entries by newlines
                    log_lines = log_data["l"].split("\\n")
                    log_lines = [line.strip() for line in log_lines if line.strip()]

                    if log_lines:
                        result += f"🔍 Found {len(log_lines)} log entries:\n\n"
                        for i, line in enumerate(log_lines, 1):
                            # Basic formatting to make logs more readable
                            if "|" in line:
                                parts = line.split("|", 3)
                                if len(parts) >= 3:
                                    timestamp = parts[0].strip()
                                    level = parts[1].strip()
                                    message = "|".join(parts[2:]).strip()
                                    result += (
                                        f"**{i}.** `{timestamp}` [{level}] {message}\n"
                                    )
                                else:
                                    result += f"**{i}.** {line}\n"
                            else:
                                result += f"**{i}.** {line}\n"
                    else:
                        result += "ℹ️ No log entries found"
                else:
                    result += "❌ No log data received from server"
            else:
                result += "❌ No response data received"

            result += f"\n\n💡 **Tip**: Use different parameters to filter results:\n"
            result += f"- `lines`: Number of entries (1-100)\n"
            result += f"- `reverse`: true for newest first, false for oldest first\n"
            result += f"- `begin_pos`: Starting position in log file"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving instance logs: {e}")
