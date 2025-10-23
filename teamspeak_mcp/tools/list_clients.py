import asyncio
from teamspeak_mcp.teamspeak_connection import TeamSpeakConnection
from mcp.server.fastmcp import FastMCP


def create_list_clients_tool(mcp: FastMCP, ts_connection: TeamSpeakConnection) -> None:

    @mcp.tool()
    def list_clients() -> str:
        """
        List all clients connected to the server
        """
        if not ts_connection.is_connected():
            raise Exception("Not connected to TeamSpeak server")

        try:
            response = ts_connection.connection.clientlist()

            # Extract clients list - response.parsed is a list of dictionaries
            if hasattr(response, "parsed"):
                clients = response.parsed
            else:
                # Fallback to container emulation
                clients = list(response)

            result = "👥 **Connected clients:**\n\n"
            for client in clients:
                client_id = client.get("clid", "N/A")
                nickname = client.get("client_nickname", "N/A")
                channel_id = client.get("cid", "N/A")
                result += f"• **ID {client_id}**: {nickname} (Channel: {channel_id})\n"

            return result
        except Exception as e:
            error_message = str(e)

            # Check for specific permission errors
            if (
                "error id 2568" in error_message
                or "insufficient client permissions" in error_message
            ):
                diagnostic_result = "❌ **Erreur de permissions insuffisantes**\n\n"
                diagnostic_result += (
                    "La commande `list_clients` nécessite des permissions élevées.\n\n"
                )
                diagnostic_result += "**🔧 Solutions possibles :**\n\n"
                diagnostic_result += "1. **Vérifiez votre mot de passe :**\n"
                diagnostic_result += (
                    "   - Utilisez un mot de passe ServerQuery valide\n"
                )
                diagnostic_result += (
                    "   - Ou utilisez un token admin (commençant par 'token=')\n\n"
                )
                diagnostic_result += "2. **Créez un utilisateur ServerQuery :**\n"
                diagnostic_result += "   ```\n"
                diagnostic_result += "   # Connectez-vous au ServerQuery\n"
                diagnostic_result += "   serverqueryadd client_login_name=mcp_user client_login_password=votre_mot_de_passe\n"
                diagnostic_result += "   servergroupaddclient sgid=6 cldbid=ID_USER  # Groupe Server Admin\n"
                diagnostic_result += "   ```\n\n"
                diagnostic_result += "3. **Obtenez un token admin :**\n"
                diagnostic_result += (
                    "   - Regardez les logs du serveur TS3 au démarrage\n"
                )
                diagnostic_result += (
                    "   - Ou utilisez: `tokenadd tokentype=0 tokenid1=6`\n\n"
                )
                diagnostic_result += "4. **Vérifiez la configuration :**\n"
                diagnostic_result += f"   - Host: {ts_connection.host}\n"
                diagnostic_result += f"   - User: {ts_connection.user}\n"
                diagnostic_result += f"   - Password: {'[SET]' if ts_connection.password else '[NOT SET]'}\n\n"
                diagnostic_result += "**🔍 Test rapide :**\n"
                diagnostic_result += "Essayez d'abord avec `server_info` qui nécessite moins de permissions."

                return diagnostic_result
            else:
                raise Exception(f"Error retrieving clients: {e}")
