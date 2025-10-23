import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_set_channel_talk_power_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def set_channel_talk_power(
        channel_id: int,
        talk_power: Optional[int] = None,
        preset: Optional[str] = None,
    ) -> str:
        """
        Set talk power requirement for a channel (useful for AFK/silent channels)
        Args:
            - channel_id: Channel ID to configure
            - talk_power: Required talk power (0=everyone can talk, 999=silent channel)
            - preset: Quick preset: 'silent' (999), 'moderated' (50), 'normal' (0)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        # Handle presets
        if preset:
            if preset == "silent":
                talk_power = 999
            elif preset == "moderated":
                talk_power = 50
            elif preset == "normal":
                talk_power = 0

        if talk_power is None:
            raise Exception("Either talk_power or preset must be specified")

        try:
            ts_connection.connection.channeledit(
                cid=channel_id,
                channel_needed_talk_power=talk_power,
            )

            preset_text = f" (preset: {preset})" if preset else ""
            result = f"✅ Talk power for channel {channel_id} set to {talk_power}{preset_text}\n"

            if talk_power == 0:
                result += "🔊 Channel is now open - everyone can talk"
            elif talk_power >= 999:
                result += (
                    "🔇 Channel is now silent - only high-privilege users can talk"
                )
            elif talk_power >= 50:
                result += "🔒 Channel is now moderated - only moderators+ can talk"
            else:
                result += f"⚡ Custom talk power requirement: {talk_power}"

            return result
        except Exception as e:
            raise Exception(f"Error setting channel talk power: {e}")
