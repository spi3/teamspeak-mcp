import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_list_privilege_tokens_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def list_privilege_tokens() -> str:
        """
        List all privilege keys/tokens available on the server
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.tokenlist()

            # Extract tokens list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                tokens = response.parsed
            else:
                # Fallback to container emulation
                tokens = list(response)

            result = "🔑 **Privilege Tokens:**\n\n"
            if not tokens:
                result += "No privilege tokens found."
            else:
                for token in tokens:
                    token_key = (
                        token.get("token", "N/A")[:20] + "..."
                        if len(token.get("token", "")) > 20
                        else token.get("token", "N/A")
                    )
                    token_type = (
                        "Server Group"
                        if token.get("token_type") == "0"
                        else (
                            "Channel Group"
                            if token.get("token_type") == "1"
                            else "Unknown"
                        )
                    )
                    token_id1 = token.get("token_id1", "N/A")
                    token_description = token.get("token_description", "No description")
                    result += f"• **Token**: {token_key}\n"
                    result += f"  - Type: {token_type} (ID: {token_id1})\n"
                    result += f"  - Description: {token_description}\n\n"

            return result
        except Exception as e:
            raise Exception(f"Error retrieving privilege tokens: {e}")
