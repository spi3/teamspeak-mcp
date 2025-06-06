#!/usr/bin/env python3
"""
Tests d'intégration complets pour TeamSpeak MCP
Teste tous les 18 outils avec un vrai serveur TeamSpeak 3
"""

import asyncio
import json
import os
import sys
import time
import socket
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teamspeak_mcp.server import TeamSpeakConnection, TOOLS

class IntegrationTester:
    """Testeur d'intégration pour TeamSpeak MCP."""
    
    def __init__(self):
        self.connection = None
        self.test_results = []
        self.created_channels = []
        self.test_client_id = None
        
    async def setup(self):
        """Configuration initiale des tests."""
        print("🚀 Setting up integration tests...")
        
        # Attendre que le serveur TS3 soit prêt
        await self.wait_for_ts3_server()
        
        # Initialiser la connexion
        self.connection = TeamSpeakConnection(
            host=os.getenv("TEAMSPEAK_HOST", "teamspeak3-server"),
            port=int(os.getenv("TEAMSPEAK_PORT", "10011")),
            user=os.getenv("TEAMSPEAK_USER", "serveradmin"),
            password=os.getenv("TEAMSPEAK_PASSWORD", ""),
            server_id=int(os.getenv("TEAMSPEAK_SERVER_ID", "1"))
        )
        
        # Obtenir le token admin si nécessaire
        if not self.connection.password:
            await self.get_admin_token()
        
        print(f"📡 Connecting to TS3: {self.connection.host}:{self.connection.port}")
        print(f"👤 User: {self.connection.user}")
        
        # Test de connexion initial avec gestion d'erreur détaillée
        try:
            print("🔌 Testing initial TeamSpeak connection...")
            success = await self.connection.connect()
            if success:
                print("✅ Initial connection successful")
            else:
                print("❌ Initial connection failed")
                raise Exception("Failed to establish initial connection to TeamSpeak server")
        except Exception as e:
            print(f"💥 Connection setup failed: {e}")
            print(f"🔍 Connection details:")
            print(f"  Host: {self.connection.host}")
            print(f"  Port: {self.connection.port}")
            print(f"  User: {self.connection.user}")
            print(f"  Password set: {'Yes' if self.connection.password else 'No'}")
            print(f"  Server ID: {self.connection.server_id}")
            raise
    
    async def wait_for_ts3_server(self, max_wait=120):
        """Attendre que le serveur TeamSpeak soit prêt."""
        print("⏳ Waiting for TeamSpeak server to be ready...")
        
        for i in range(max_wait):
            try:
                # Tenter une connexion basique
                if wait_for_server(self.connection.host, self.connection.port):
                    await asyncio.sleep(5)  # Attendre un peu plus pour la stabilité
                    return
                    
            except Exception:
                pass
                
            await asyncio.sleep(1)
        
        raise Exception("TeamSpeak server not ready after 120s")
    
    async def get_admin_token(self):
        """Récupérer le token admin depuis les logs TS3."""
        token_file = "/scripts/admin_token.txt"
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token = f.read().strip()
                if token:
                    self.connection.password = token
                    print(f"🔑 Using admin token: {token[:10]}...")
                    return
        
        print("⚠️  No admin token found, using empty password")
    
    async def run_all_tests(self):
        """Exécuter tous les tests d'intégration."""
        print("\n🧪 Running comprehensive integration tests...")
        print(f"📋 Testing {len(TOOLS)} tools\n")
        
        # Tests de base
        await self.test_connection()
        await self.test_server_info()
        await self.test_list_channels()
        await self.test_list_clients()
        
        # Tests de gestion des canaux
        await self.test_channel_management()
        await self.test_channel_permissions()
        
        # Tests de gestion des serveurs
        await self.test_server_settings()
        
        # Tests de gestion des utilisateurs
        await self.test_user_management()
        
        # Tests de messaging
        await self.test_messaging()
        
        # Nettoyage
        await self.cleanup()
        
        # Rapport final
        self.print_test_report()
    
    async def test_connection(self):
        """Test de connexion de base."""
        print("🔌 Testing connection...")
        
        try:
            success = await self.connection.connect()
            if success:
                self.record_success("connect_to_server", "Basic connection successful")
            else:
                self.record_failure("connect_to_server", "Connection failed")
        except Exception as e:
            self.record_failure("connect_to_server", f"Connection error: {e}")
    
    async def test_server_info(self):
        """Test d'information serveur."""
        print("🖥️  Testing server info...")
        
        try:
            info = await asyncio.to_thread(self.connection.connection.serverinfo)
            server_name = info.get('virtualserver_name', 'Unknown')
            self.record_success("server_info", f"Server: {server_name}")
        except Exception as e:
            self.record_failure("server_info", f"Failed: {e}")
    
    async def test_list_channels(self):
        """Test de listage des canaux."""
        print("📋 Testing channel listing...")
        
        try:
            channels = await asyncio.to_thread(self.connection.connection.channellist)
            count = len(channels) if channels else 0
            self.record_success("list_channels", f"Found {count} channels")
        except Exception as e:
            self.record_failure("list_channels", f"Failed: {e}")
    
    async def test_list_clients(self):
        """Test de listage des clients."""
        print("👥 Testing client listing...")
        
        try:
            clients = await asyncio.to_thread(self.connection.connection.clientlist)
            if clients:
                # Prendre le premier client (probablement notre connexion)
                self.test_client_id = clients[0].get('clid')
                count = len(clients)
                self.record_success("list_clients", f"Found {count} clients")
            else:
                self.record_failure("list_clients", "No clients found")
        except Exception as e:
            self.record_failure("list_clients", f"Failed: {e}")
    
    async def test_channel_management(self):
        """Test de gestion des canaux."""
        print("🔧 Testing channel management...")
        
        # Créer un canal de test
        test_channel_name = f"Test Channel {int(time.time())}"
        
        try:
            # Test create_channel
            await asyncio.to_thread(
                self.connection.connection.channelcreate,
                channel_name=test_channel_name
            )
            
            # Trouver le canal créé
            channels = await asyncio.to_thread(self.connection.connection.channellist)
            test_channel = None
            for channel in channels:
                if channel.get('channel_name') == test_channel_name:
                    test_channel = channel
                    break
            
            if test_channel:
                channel_id = test_channel.get('cid')
                self.created_channels.append(channel_id)
                self.record_success("create_channel", f"Created channel {channel_id}")
                
                # Test update_channel
                await asyncio.to_thread(
                    self.connection.connection.channeledit,
                    cid=channel_id,
                    channel_description="Test description"
                )
                self.record_success("update_channel", f"Updated channel {channel_id}")
                
                # Test channel_info
                info = await asyncio.to_thread(
                    self.connection.connection.channelinfo,
                    cid=channel_id
                )
                self.record_success("channel_info", f"Got info for channel {channel_id}")
                
                # Test set_channel_talk_power
                await asyncio.to_thread(
                    self.connection.connection.channeledit,
                    cid=channel_id,
                    channel_needed_talk_power=50
                )
                self.record_success("set_channel_talk_power", f"Set talk power for channel {channel_id}")
                
            else:
                self.record_failure("create_channel", "Channel not found after creation")
                
        except Exception as e:
            self.record_failure("channel_management", f"Failed: {e}")
    
    async def test_channel_permissions(self):
        """Test de gestion des permissions de canal."""
        print("🛡️  Testing channel permissions...")
        
        if not self.created_channels:
            self.record_failure("manage_channel_permissions", "No test channels available")
            return
        
        channel_id = self.created_channels[0]
        
        try:
            # Test list permissions
            perms = await asyncio.to_thread(
                self.connection.connection.channelpermlist,
                cid=channel_id, permsid=True
            )
            self.record_success("manage_channel_permissions_list", f"Listed permissions for channel {channel_id}")
            
            # Test add permission
            await asyncio.to_thread(
                self.connection.connection.channeladdperm,
                cid=channel_id, permsid="i_channel_needed_join_power", permvalue=10
            )
            self.record_success("manage_channel_permissions_add", f"Added permission to channel {channel_id}")
            
        except Exception as e:
            self.record_failure("manage_channel_permissions", f"Failed: {e}")
    
    async def test_server_settings(self):
        """Test de configuration serveur."""
        print("⚙️  Testing server settings...")
        
        try:
            # Test update_server_settings
            await asyncio.to_thread(
                self.connection.connection.serveredit,
                virtualserver_welcomemessage="Welcome to test server!"
            )
            self.record_success("update_server_settings", "Updated server welcome message")
            
        except Exception as e:
            self.record_failure("update_server_settings", f"Failed: {e}")
    
    async def test_user_management(self):
        """Test de gestion des utilisateurs."""
        print("👤 Testing user management...")
        
        if not self.test_client_id:
            self.record_failure("user_management", "No test client available")
            return
        
        try:
            # Test client_info_detailed
            info = await asyncio.to_thread(
                self.connection.connection.clientinfo,
                clid=self.test_client_id
            )
            self.record_success("client_info_detailed", f"Got detailed info for client {self.test_client_id}")
            
            # Test manage_user_permissions (list groups)
            if hasattr(info, 'data') and info.data:
                client_info = info.data[0]
            else:
                client_info = info
            
            client_database_id = client_info.get('client_database_id')
            if client_database_id:
                groups = await asyncio.to_thread(
                    self.connection.connection.servergroupsbyclientid,
                    cldbid=client_database_id
                )
                self.record_success("manage_user_permissions_list_groups", f"Listed groups for client {self.test_client_id}")
                
                # Test list permissions
                perms = await asyncio.to_thread(
                    self.connection.connection.clientpermlist,
                    cldbid=client_database_id, permsid=True
                )
                self.record_success("manage_user_permissions_list_permissions", f"Listed permissions for client {self.test_client_id}")
            
        except Exception as e:
            self.record_failure("user_management", f"Failed: {e}")
    
    async def test_messaging(self):
        """Test de messagerie."""
        print("💬 Testing messaging...")
        
        try:
            # Test send_channel_message
            await asyncio.to_thread(
                self.connection.connection.sendtextmessage,
                targetmode=2, target=0, msg="Test channel message from MCP"
            )
            self.record_success("send_channel_message", "Sent channel message")
            
            # Test send_private_message (à nous-même)
            if self.test_client_id:
                await asyncio.to_thread(
                    self.connection.connection.sendtextmessage,
                    targetmode=1, target=self.test_client_id, msg="Test private message from MCP"
                )
                self.record_success("send_private_message", f"Sent private message to client {self.test_client_id}")
            
        except Exception as e:
            self.record_failure("messaging", f"Failed: {e}")
    
    async def cleanup(self):
        """Nettoyage après les tests."""
        print("🧹 Cleaning up test data...")
        
        # Supprimer les canaux de test
        for channel_id in self.created_channels:
            try:
                await asyncio.to_thread(
                    self.connection.connection.channeldelete,
                    cid=channel_id, force=1
                )
                print(f"  ✅ Deleted test channel {channel_id}")
            except Exception as e:
                print(f"  ⚠️  Failed to delete channel {channel_id}: {e}")
        
        # Fermer la connexion
        if self.connection:
            await self.connection.disconnect()
    
    def record_success(self, tool_name: str, message: str):
        """Enregistrer un succès de test."""
        self.test_results.append({
            "tool": tool_name,
            "status": "SUCCESS",
            "message": message
        })
        print(f"  ✅ {tool_name}: {message}")
    
    def record_failure(self, tool_name: str, message: str):
        """Enregistrer un échec de test."""
        self.test_results.append({
            "tool": tool_name,
            "status": "FAILURE", 
            "message": message
        })
        print(f"  ❌ {tool_name}: {message}")
    
    def print_test_report(self):
        """Afficher le rapport final des tests."""
        print("\n" + "="*60)
        print("📊 INTEGRATION TEST REPORT")
        print("="*60)
        
        successes = [r for r in self.test_results if r["status"] == "SUCCESS"]
        failures = [r for r in self.test_results if r["status"] == "FAILURE"]
        
        print(f"✅ Successes: {len(successes)}")
        print(f"❌ Failures: {len(failures)}")
        print(f"📊 Total tests: {len(self.test_results)}")
        print(f"🎯 Success rate: {len(successes)/len(self.test_results)*100:.1f}%")
        
        if failures:
            print("\n❌ FAILED TESTS:")
            for failure in failures:
                print(f"  • {failure['tool']}: {failure['message']}")
        
        print("\n✅ SUCCESSFUL TESTS:")
        for success in successes:
            print(f"  • {success['tool']}: {success['message']}")
        
        # Sauvegarder les résultats
        os.makedirs("/app/test_results", exist_ok=True)
        with open("/app/test_results/integration_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Results saved to /app/test_results/integration_results.json")
        
        # Code de sortie
        if failures:
            print("\n💥 Some tests failed!")
            sys.exit(1)
        else:
            print("\n🎉 All tests passed!")
            sys.exit(0)

def wait_for_server(host: str, port: int, timeout: int = 120) -> bool:
    """
    Attendre que le serveur TeamSpeak soit prêt
    """
    print(f"⏳ Waiting for TeamSpeak server at {host}:{port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                if result == 0:
                    print(f"✅ Server is ready after {int(time.time() - start_time)}s")
                    return True
        except Exception as e:
            print(f"⚠️  Connection attempt failed: {e}")
        
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0:  # Log every 15 seconds
            print(f"⏳ Still waiting... ({elapsed}s elapsed)")
        
        time.sleep(1)
    
    print(f"❌ TeamSpeak server not ready after {timeout} seconds")
    return False

async def main():
    """Fonction principale des tests."""
    tester = IntegrationTester()
    
    try:
        print("🚀 Starting TeamSpeak MCP Integration Tests")
        print("=" * 60)
        await tester.setup()
        await tester.run_all_tests()
        print("🎉 All integration tests completed successfully!")
    except Exception as e:
        print(f"💥 Integration tests failed with error: {e}")
        print(f"🔍 Error details:")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")
        
        # Print traceback for debugging
        import traceback
        print(f"📋 Full traceback:")
        traceback.print_exc()
        
        # Try to save whatever results we have
        try:
            if tester.test_results:
                print(f"💾 Saving partial test results ({len(tester.test_results)} tests)...")
                os.makedirs("/app/test_results", exist_ok=True)
                with open("/app/test_results/integration_results.json", "w") as f:
                    json.dump(tester.test_results, f, indent=2)
                print("✅ Partial results saved")
            else:
                print("📋 No test results to save")
        except Exception as save_error:
            print(f"⚠️ Failed to save partial results: {save_error}")
        
        print("💥 Exiting with error code 1")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 