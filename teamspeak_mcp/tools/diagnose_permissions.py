import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_diagnose_permissions_tool(
    mcp: FastMCP, ts_connection: TeamSpeakConnection
) -> None:

    @mcp.tool()
    def diagnose_permissions() -> str:
        """
        Diagnose current connection permissions and provide troubleshooting help
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        result = "🔍 **Diagnostic des Permissions TeamSpeak MCP**\n\n"

        # Test 1: Basic whoami
        try:
            whoami_response = ts_connection.connection.whoami()

            if hasattr(whoami_response, "parsed") and whoami_response.parsed:
                whoami = whoami_response.parsed[0]
            elif hasattr(whoami_response, "__getitem__"):
                whoami = whoami_response[0]
            else:
                raise Exception("Could not parse whoami response")

            result += "✅ **Connexion de base** : OK\n"
            result += f"   - Client ID: {whoami.get('client_id', 'N/A')}\n"
            result += f"   - Database ID: {whoami.get('client_database_id', 'N/A')}\n"
            result += f"   - Nickname: {whoami.get('client_nickname', 'N/A')}\n"
            result += f"   - Type: {'ServerQuery' if whoami.get('client_type') == '1' else 'Regular'}\n\n"

            # Store client_database_id for later use
            client_db_id = whoami.get("client_database_id")

        except Exception as e:
            result += f"❌ **Connexion de base** : ÉCHEC\n   Erreur: {e}\n\n"
            return result

        # Test 2: Server info (basic permission)
        try:
            ts_connection.connection.serverinfo()
            result += "✅ **server_info** : OK (permissions de base)\n"
        except Exception as e:
            result += f"❌ **server_info** : ÉCHEC - {e}\n"

        # Test 3: Client list (elevated permission)
        try:
            ts_connection.connection.clientlist()
            result += "✅ **list_clients** : OK (permissions élevées)\n"
        except Exception as e:
            result += f"❌ **list_clients** : ÉCHEC - {e}\n"

        # Test 4: Channel list
        try:
            ts_connection.connection.channellist()
            result += "✅ **list_channels** : OK\n"
        except Exception as e:
            result += f"❌ **list_channels** : ÉCHEC - {e}\n"

        # Test 5: Try to get current permissions
        try:
            if client_db_id and client_db_id != "N/A":
                # Try to get server groups
                try:
                    groups_response = ts_connection.connection.servergroupsbyclientid(
                        cldbid=client_db_id,
                    )

                    if hasattr(groups_response, "parsed"):
                        groups = groups_response.parsed
                    else:
                        groups = list(groups_response)

                    result += f"✅ **Groupes serveur** : OK\n"
                    for group in groups[:3]:  # Limit to first 3 groups
                        group_name = group.get("name", "N/A")
                        group_id = group.get("sgid", "N/A")
                        result += f"   - {group_name} (ID: {group_id})\n"

                except Exception as e:
                    result += f"❌ **Groupes serveur** : ÉCHEC - {e}\n"
            else:
                result += (
                    f"⚠️ **Groupes serveur** : Impossible (pas de client_database_id)\n"
                )

        except Exception as e:
            result += f"❌ **Analyse des permissions** : ÉCHEC - {e}\n"

        result += "\n**📊 Configuration actuelle :**\n"
        result += f"   - Host: {ts_connection.host}:{ts_connection.port}\n"
        result += f"   - User: {ts_connection.user}\n"
        result += f"   - Password: {'✅ Fourni' if ts_connection.password else '❌ Non fourni'}\n"
        result += f"   - Server ID: {ts_connection.server_id}\n\n"

        result += "**💡 Recommandations :**\n\n"
        result += "Si vous avez des échecs :\n"
        result += "1. **Vérifiez votre mot de passe ServerQuery**\n"
        result += "2. **Utilisez un token admin** si disponible\n"
        result += "3. **Créez un utilisateur ServerQuery avec permissions admin**\n"
        result += "4. **Vérifiez que le port 10011 (ServerQuery) est accessible**\n\n"
        result += "Pour plus d'aide, utilisez la commande `list_clients` qui fournit un diagnostic détaillé en cas d'erreur."

        return result
