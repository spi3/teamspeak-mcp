import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_channel_info_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def channel_info(channel_id: int) -> str:
        """
        Get detailed information about a specific channel
        Args:
            - channel_id: Channel ID to get info for
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.channelinfo(cid=channel_id)

            # Extract the first (and usually only) result
            if hasattr(response, "parsed") and response.parsed:
                info = response.parsed[0]
            elif hasattr(response, "__getitem__"):
                # Use container emulation
                info = response[0]
            else:
                raise Exception("Unexpected response format")

            result = "📋 **Channel Information:**\n\n"
            result += f"• **ID**: {info.get('cid', 'N/A')}\n"
            result += f"• **Name**: {info.get('channel_name', 'N/A')}\n"
            result += f"• **Description**: {info.get('channel_description', 'N/A')}\n"
            result += f"• **Topic**: {info.get('channel_topic', 'N/A')}\n"
            result += f"• **Password Protected**: {'Yes' if info.get('channel_flag_password') == '1' else 'No'}\n"
            result += (
                f"• **Max Clients**: {info.get('channel_maxclients', 'Unlimited')}\n"
            )
            result += f"• **Current Clients**: {info.get('total_clients', '0')}\n"
            result += f"• **Talk Power Required**: {info.get('channel_needed_talk_power', '0')}\n"
            result += f"• **Codec**: {info.get('channel_codec', 'N/A')}\n"
            result += (
                f"• **Codec Quality**: {info.get('channel_codec_quality', 'N/A')}\n"
            )
            result += f"• **Type**: {'Permanent' if info.get('channel_flag_permanent') == '1' else 'Temporary'}\n"
            result += f"• **Order**: {info.get('channel_order', 'N/A')}\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving channel info: {e}")
