import asyncio
import logging
from time import sleep
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def create_view_server_logs_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def view_server_logs(
        lines: int = 50,
        reverse: bool = True,
        instance_log: bool = False,
        begin_pos: Optional[int] = None,
        log_level: Optional[int] = None,
        timestamp_from: Optional[int] = None,
        timestamp_to: Optional[int] = None,
        complete_mode: bool = False,
        max_iterations: int = 1000,
        enhanced_debug: bool = False,
    ) -> str:
        """
        View recent entries from the virtual server log with enhanced options
        Args:
            - lines: Number of log lines to retrieve (1-100, default: 50)
            - reverse: Show logs in reverse order (newest first, default: true)
            - instance_log: Show instance log instead of virtual server log (default: false)
            - begin_pos: Starting position in log file (optional)
            - log_level: Log level (1=ERROR, 2=WARNING, 3=DEBUG, 4=INFO)
            - timestamp_from: Unix timestamp for log entries from (optional)
            - timestamp_to: Unix timestamp for log entries to (optional)
            - complete_mode: Enable complete mode - retrieve ALL logs by paginating automatically (default: false)
            - max_iterations: Maximum pagination iterations in complete mode (default: 1000)
            - enhanced_debug: Enable enhanced debugging information (default: false)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            if complete_mode:
                # Complete mode with automatic pagination
                return _view_server_logs_complete_impl(
                    lines, reverse, instance_log, max_iterations, enhanced_debug
                )
            elif enhanced_debug:
                # Enhanced debug mode
                return _view_server_logs_enhanced_impl(
                    lines, reverse, instance_log, begin_pos, enhanced_debug
                )
            else:
                # Standard enhanced mode
                kwargs = {}
                if lines:
                    kwargs["lines"] = lines
                if reverse is not None:
                    kwargs["reverse"] = 1 if reverse else 0
                if instance_log:
                    kwargs["instance"] = 1
                if begin_pos:
                    kwargs["begin_pos"] = begin_pos

                # Try enhanced parameters (may not be supported on all TS versions)
                if log_level:
                    kwargs["loglevel"] = log_level
                if timestamp_from:
                    kwargs["timestamp_begin"] = timestamp_from
                if timestamp_to:
                    kwargs["timestamp_end"] = timestamp_to

                logger.info(f"Executing logview with parameters: {kwargs}")
                response = ts_connection.connection.logview(**kwargs)

                # Enhanced log data extraction
                if hasattr(response, "parsed") and response.parsed:
                    log_data = response.parsed[0] if response.parsed else {}
                else:
                    log_data = response[0] if response else {}

                result = "📋 **Server Logs Enhanced:**\n\n"
                result += f"**Parameters used:** lines={lines}, reverse={reverse}, instance_log={instance_log}\n"
                if log_level:
                    result += f"**Log level:** {log_level}\n"
                result += "\n"

                # Multiple ways to extract log entries
                log_entries = []

                # Method 1: Standard 'l' field
                if "l" in log_data:
                    entries = log_data["l"].split("\\n")
                    log_entries.extend(
                        [entry.strip() for entry in entries if entry.strip()]
                    )

                # Method 2: Check for alternative fields
                for field in ["log", "logentry", "entries", "data"]:
                    if field in log_data:
                        if isinstance(log_data[field], str):
                            entries = log_data[field].split("\\n")
                            log_entries.extend(
                                [entry.strip() for entry in entries if entry.strip()]
                            )
                        elif isinstance(log_data[field], list):
                            log_entries.extend(log_data[field])

                # Method 3: If log_data is a list itself
                if isinstance(log_data, list):
                    for item in log_data:
                        if isinstance(item, str):
                            log_entries.append(item.strip())
                        elif isinstance(item, dict) and "l" in item:
                            entries = item["l"].split("\\n")
                            log_entries.extend(
                                [entry.strip() for entry in entries if entry.strip()]
                            )

                # Method 4: Raw response processing if nothing else works
                if not log_entries:
                    raw_response = str(response)
                    if "|" in raw_response:  # TeamSpeak log format has | separators
                        potential_logs = raw_response.split("\n")
                        for line in potential_logs:
                            if "|" in line and any(
                                level in line
                                for level in ["INFO", "ERROR", "WARNING", "DEBUG"]
                            ):
                                log_entries.append(line.strip())

                if log_entries:
                    result += f"**{len(log_entries)} entries found:**\n\n"
                    for i, entry in enumerate(
                        log_entries[-lines:], 1
                    ):  # Take last N lines
                        if entry:
                            result += f"**{i}.** {entry}\n"
                else:
                    result += "❌ **No log entries found.**\n\n"
                    result += "**Raw data received:**\n"
                    result += f"```\n{str(log_data)[:500]}...\n```\n"
                    result += "\n**Suggestion:** Check the configuration of TeamSpeak server logs."

                # Additional debugging info
                result += f"\n**Debug info:**\n"
                result += f"- Response type: {type(response)}\n"
                result += f"- Available keys: {list(log_data.keys()) if isinstance(log_data, dict) else 'Not dict'}\n"
                result += f"- Data size: {len(str(log_data))} characters\n"

                return result

        except Exception as e:
            raise Exception(f"Error retrieving server logs: {e}")

    def _view_server_logs_complete_impl(
        lines: int,
        reverse: bool,
        instance_log: bool,
        max_iterations: int,
        enhanced_debug: bool,
    ) -> str:
        """
        Retrieve ALL server logs with automatic pagination
        Based on using begin_pos with last_pos to retrieve everything
        """
        all_logs = []
        current_pos = None
        iteration = 0

        try:
            while iteration < max_iterations:
                # Parameters for logview request
                params = {
                    "lines": min(lines, 100),  # Maximum 100 lines per request
                    "reverse": 1 if reverse else 0,
                    "instance": 1 if instance_log else 0,
                }

                # Add begin_pos only if we have it (after first request)
                if current_pos is not None:
                    params["begin_pos"] = current_pos
                    params["lines"] = (
                        1  # Get only 1 line at a time to avoid incomplete lines
                    )

                # Execute logview request
                response = ts_connection.connection.logview(**params)

                # Check if we have data
                if not hasattr(response, "parsed") or not response.parsed:
                    break

                # Extract logs from this batch
                logs_batch = []
                for entry in response.parsed:
                    if "l" in entry:  # 'l' contains the log text
                        logs_batch.append(entry["l"])

                # If no new logs, we're done
                if not logs_batch:
                    break

                # Add to our collection
                all_logs.extend(logs_batch)

                # Get last_pos for next iteration
                if hasattr(response, "last_pos"):
                    new_pos = getattr(response, "last_pos", None)
                    if new_pos == 0 or new_pos == current_pos:
                        # last_pos = 0 means we reached the end
                        break
                    current_pos = new_pos
                else:
                    # No last_pos, stop
                    break

                iteration += 1

                # Small delay to avoid spamming the server
                sleep(0.1)

        except Exception as e:
            # Log error but return what we already retrieved
            logger.error(f"Error retrieving logs: {e}")

        # Format output
        if not all_logs:
            result = "No logs found"
        else:
            formatted_logs = []
            for i, log_line in enumerate(all_logs, 1):
                formatted_logs.append(f"**{i}.** {log_line}")

            result = f"""📋 **Server Logs Complete (Enhanced):**

**Parameters used:** lines={lines}, reverse={reverse}, instance_log={instance_log}

**{len(all_logs)} entries found:**

{chr(10).join(formatted_logs)}

**Retrieval stats:**
- Iterations: {iteration}
- Final position: {current_pos}
- Total logs: {len(all_logs)}
"""

        return result

    async def _view_server_logs_enhanced_impl(
        lines: int,
        reverse: bool,
        instance_log: bool,
        begin_pos: Optional[int],
        enhanced_debug: bool,
    ) -> str:
        """
        Enhanced version with better error handling
        """
        try:
            # Base configuration
            params = {
                "lines": min(lines, 100),  # TeamSpeak limits to 100
                "reverse": 1 if reverse else 0,
                "instance": 1 if instance_log else 0,
            }

            if begin_pos is not None:
                params["begin_pos"] = begin_pos

            # Execute request
            response = await asyncio.to_thread(
                ts_connection.connection.logview, **params
            )

            # Debug info
            debug_info = {
                "response_type": str(type(response)),
                "has_parsed": hasattr(response, "parsed"),
                "has_last_pos": hasattr(response, "last_pos"),
                "has_file_size": hasattr(response, "file_size"),
            }

            # Extract logs
            logs = []
            if hasattr(response, "parsed") and response.parsed:
                for entry in response.parsed:
                    if isinstance(entry, dict) and "l" in entry:
                        logs.append(entry["l"])
                    elif isinstance(entry, str):
                        logs.append(entry)

            # Pagination information
            last_pos = getattr(response, "last_pos", None)
            file_size = getattr(response, "file_size", None)

            # Format result
            result = f"""📋 **Server Logs Enhanced:**

**Parameters used:** lines={lines}, reverse={reverse}, instance_log={instance_log}

**{len(logs)} entries found:**

"""

            for i, log_line in enumerate(logs, 1):
                result += f"**{i}.** {log_line}\n"

            result += f"""
**Debug info:**
- Response type: {debug_info['response_type']}
- Has parsed: {debug_info['has_parsed']}
- Has last_pos: {debug_info['has_last_pos']} (value: {last_pos})
- Has file_size: {debug_info['has_file_size']} (value: {file_size})
- Data size: {len(str(response))} characters

**Pagination info:**
- Current position: {begin_pos}
- Next position: {last_pos}
- More data available: {'Yes' if last_pos and last_pos > 0 else 'No'}
"""

            return result

        except Exception as e:
            result = f"❌ **Error retrieving server logs:**\n\nError: {str(e)}\nType: {type(e).__name__}"
            return result
