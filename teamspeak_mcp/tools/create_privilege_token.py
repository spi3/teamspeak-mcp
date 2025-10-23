import asyncio
from typing import Optional
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_create_privilege_token_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def create_privilege_token(
        token_type: int,
        group_id: int,
        channel_id: Optional[int] = None,
        description: Optional[str] = None,
        custom_set: Optional[str] = None,
    ) -> str:
        """
        Create a new privilege key/token for server or channel group access
        Args:
            - token_type: Token type (0=server group, 1=channel group)
            - group_id: Server group ID (for token_type=0) or channel group ID (for token_type=1)
            - channel_id: Channel ID (required for channel group tokens when token_type=1)
            - description: Optional description for the token
            - custom_set: Optional custom client properties set (format: ident=value|ident=value)
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.tokenadd(
                tokentype=token_type,
                tokenid1=group_id,
                tokenid2=channel_id if channel_id else 0,
                tokendescription=description if description else "",
                tokencustomset=custom_set if custom_set else "",
            )

            # Extract the token from response
            if hasattr(response, "parsed") and response.parsed:
                token_info = response.parsed[0]
                token = token_info.get("token", "N/A")
                result = f"✅ Privilege token created successfully\n"
                result += f"🔑 **Token**: {token}"
            else:
                result = f"✅ Privilege token created successfully"

            return result
        except Exception as e:
            raise Exception(f"Error creating privilege token: {e}")
