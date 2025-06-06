#!/usr/bin/env python3
"""
Interactive installation script for TeamSpeak MCP.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

def print_banner():
    """Display installation banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🎮 TeamSpeak MCP Installer                 ║
║          Configure your MCP server for Claude                ║
╚══════════════════════════════════════════════════════════════╝
""")

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def collect_teamspeak_config():
    """Collect TeamSpeak configuration from user."""
    print("\n🔧 TeamSpeak Configuration")
    print("Please enter your TeamSpeak server information:\n")
    
    config = {}
    
    # Host
    host = input("📍 TeamSpeak server address: ").strip()
    while not host:
        host = input("❌ Address is required. Try again: ").strip()
    config["TEAMSPEAK_HOST"] = host
    
    # Port
    port = input("🔌 ServerQuery port (default: 10011): ").strip()
    config["TEAMSPEAK_PORT"] = port if port else "10011"
    
    # User
    user = input("👤 ServerQuery username (default: serveradmin): ").strip()
    config["TEAMSPEAK_USER"] = user if user else "serveradmin"
    
    # Password
    password = input("🔒 ServerQuery password: ").strip()
    while not password:
        password = input("❌ Password is required. Try again: ").strip()
    config["TEAMSPEAK_PASSWORD"] = password
    
    # Server ID
    server_id = input("🆔 Virtual server ID (default: 1): ").strip()
    config["TEAMSPEAK_SERVER_ID"] = server_id if server_id else "1"
    
    return config

def create_env_file(config):
    """Create .env file with configuration."""
    print("\n📄 Creating configuration file...")
    
    try:
        with open(".env", "w") as f:
            f.write("# TeamSpeak MCP Configuration\n")
            f.write("# Generated automatically by installer\n\n")
            
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def find_claude_config_path():
    """Find Claude Desktop configuration path."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"  
    else:  # Linux
        return Path.home() / ".config/claude/claude_desktop_config.json"

def update_claude_config(ts_config):
    """Update Claude Desktop configuration."""
    print("\n🤖 Configuring Claude Desktop...")
    
    claude_config_path = find_claude_config_path()
    print(f"📍 Claude configuration path: {claude_config_path}")
    
    # Create directory if needed
    claude_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing configuration or create new
    if claude_config_path.exists():
        try:
            with open(claude_config_path, 'r') as f:
                claude_config = json.load(f)
        except json.JSONDecodeError:
            claude_config = {}
    else:
        claude_config = {}
    
    # Add TeamSpeak MCP configuration
    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}
    
    claude_config["mcpServers"]["teamspeak"] = {
        "command": "python",
        "args": ["-m", "teamspeak_mcp.server"],
        "env": ts_config
    }
    
    # Save configuration
    try:
        with open(claude_config_path, 'w') as f:
            json.dump(claude_config, f, indent=2)
        
        print("✅ Claude Desktop configuration updated")
        return True
    except Exception as e:
        print(f"❌ Error updating Claude configuration: {e}")
        print(f"💡 You can manually copy the content from claude_desktop_config.json")
        return False

def test_installation():
    """Test the installation."""
    print("\n🧪 Testing installation...")
    
    try:
        subprocess.check_call([sys.executable, "test_mcp.py"])
        return True
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        return False

def main():
    """Main installation function."""
    print_banner()
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # TeamSpeak configuration
    ts_config = collect_teamspeak_config()
    
    # Create .env file
    if not create_env_file(ts_config):
        sys.exit(1)
    
    # Claude Desktop configuration
    claude_updated = update_claude_config(ts_config)
    
    # Test installation
    test_success = test_installation()
    
    # Summary
    print("\n" + "="*60)
    print("📋 INSTALLATION SUMMARY")
    print("="*60)
    print(f"✅ Dependencies installed")
    print(f"✅ TeamSpeak configuration created")
    print(f"{'✅' if claude_updated else '❌'} Claude Desktop configuration")
    print(f"{'✅' if test_success else '❌'} Installation tests")
    
    if claude_updated and test_success:
        print("\n🎉 Installation completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Restart Claude Desktop")
        print("2. Open a new conversation")
        print("3. Test with: 'Connect to TeamSpeak server'")
        print("4. Use: 'List connected users'")
    else:
        print("\n⚠️  Installation partially successful")
        if not claude_updated:
            print("💡 Manually configure Claude Desktop with claude_desktop_config.json")
        if not test_success:
            print("💡 Check your TeamSpeak configuration in .env")

if __name__ == "__main__":
    main() 