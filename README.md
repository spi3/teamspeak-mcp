# TeamSpeak MCP

A Model Context Protocol (MCP) server for controlling TeamSpeak from AI models like Claude.

## Requirements

- **Python 3.10-3.12** 
- **Docker** (optional, for containerized deployment)
- **TeamSpeak 3 Server** with ServerQuery enabled

## Features

- 🎯 Connect to TeamSpeak servers
- 💬 Send messages to channels and private messages
- 📋 List connected users
- 🔧 Channel management (create, delete, move users)
- 🎵 Voice control (mute, unmute, kick, ban)
- 📊 Server statistics

## 🎯 **Integration Methods Overview**

TeamSpeak MCP offers multiple integration methods to fit your setup and preferences:

### **📦 Method 1: PyPI Package (Recommended for most users)**
- ✅ **Easiest setup** - One command installation
- ✅ **Automatic updates** via standard package managers
- ✅ **Standard MCP pattern** - Compatible with Claude Desktop examples
- ✅ **No Docker required** - Pure Python implementation

```bash
# Installation
uvx install teamspeak-mcp

# Usage
uvx teamspeak-mcp --host your-server.com --user your-user --password your-password

# Claude Desktop config (CLI args)
{
  "mcpServers": {
    "teamspeak": {
      "command": "uvx",
      "args": ["teamspeak-mcp", "--host", "your-server.com", "--user", "your-user", "--password", "your-password"]
    }
  }
}
```

### **🐳 Method 2: Pre-built Docker Images (Recommended for containers)**
- ✅ **No dependencies** - Everything included
- ✅ **Version consistency** - Immutable deployments  
- ✅ **Easy scaling** - Works with orchestration
- ✅ **Cross-platform** - Works anywhere Docker runs

> **💡 Note**: We use `-e` flags in args instead of the `"env": {}` field because Claude Desktop's environment variable handling can be unreliable. The args method ensures consistent variable passing.

```bash
# Installation
docker pull ghcr.io/marlburrow/teamspeak-mcp:latest

# Claude Desktop config (env vars in args)
{
  "mcpServers": {
    "teamspeak": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TEAMSPEAK_HOST=your-server.com",
        "-e", "TEAMSPEAK_USER=your-user", 
        "-e", "TEAMSPEAK_PASSWORD=your-password",
        "ghcr.io/marlburrow/teamspeak-mcp:latest"
      ]
    }
  }
}
```

### **🐍 Method 3: Local Python Installation (For developers)**
- ✅ **Full control** - Access to source code
- ✅ **Customizable** - Modify for specific needs
- ✅ **Development** - Contribute to the project
- ⚠️ **More setup** - Requires Python environment management

```bash
# Installation
git clone https://github.com/MarlBurroW/teamspeak-mcp.git
cd teamspeak-mcp && pip install -r requirements.txt

# Claude Desktop config (Python module)
{
  "mcpServers": {
    "teamspeak": {
      "command": "python",
      "args": ["-m", "teamspeak_mcp.server", "--host", "your-server.com", "--user", "your-user", "--password", "your-password"]
    }
  }
}
```

### **🏗️ Method 4: Local Docker Build (For customization)**
- ✅ **Custom builds** - Modify Dockerfile as needed
- ✅ **Offline capability** - No external dependencies
- ✅ **Version control** - Pin to specific commits
- ⚠️ **Build time** - Requires local Docker build

```bash
# Installation
git clone https://github.com/MarlBurroW/teamspeak-mcp.git
cd teamspeak-mcp && docker build -t teamspeak-mcp .

# Claude Desktop config (local image)
{
  "mcpServers": {
    "teamspeak": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TEAMSPEAK_HOST=your-server.com",
        "-e", "TEAMSPEAK_USER=your-user",
        "-e", "TEAMSPEAK_PASSWORD=your-password",
        "teamspeak-mcp"
      ]
    }
  }
}
```

### **🎯 Which Method Should You Choose?**

| Use Case | Recommended Method | Why |
|----------|-------------------|-----|
| **First time user** | PyPI Package (`uvx`) | Easiest setup, standard MCP pattern |
| **Production deployment** | Pre-built Docker | Reliable, versioned, no dependencies |
| **CI/CD environments** | Pre-built Docker | Consistent, fast deployment |
| **Development/Contributing** | Local Python | Full access to source code |
| **Custom modifications** | Local Docker Build | Controlled build process |
| **Corporate environments** | Local Docker Build | No external dependencies |

### **💡 Quick Start Examples**

**Fastest (PyPI):**
```bash
uvx install teamspeak-mcp
# Add to Claude Desktop config with CLI args
```

**Most Reliable (Docker):**
```bash
docker pull ghcr.io/marlburrow/teamspeak-mcp:latest
# Add to Claude Desktop config with env vars in args
```

**Most Flexible (Local):**
```bash
git clone https://github.com/MarlBurroW/teamspeak-mcp.git
cd teamspeak-mcp && pip install -r requirements.txt
# Add to Claude Desktop config with Python module
```

## 🚀 Quick Start

### Automatic installation script
```bash
python install.py
```

### Connection test
```bash
python test_mcp.py
```

### With Docker
```bash
# Build image
docker build -t teamspeak-mcp .

# Test with Docker
docker run --rm -it \
  -e TEAMSPEAK_HOST=your-server.com \
  -e TEAMSPEAK_USER=your-user \
  -e TEAMSPEAK_PASSWORD=your-password \
  teamspeak-mcp test
```

## 🔑 TeamSpeak Server Setup

Before using TeamSpeak MCP, you need to configure your TeamSpeak server credentials:

### **📋 Required Information**

| Parameter | Description | Example |
|-----------|-------------|---------|
| **TEAMSPEAK_HOST** | Your server IP or domain | `ts.example.com` or `192.168.1.100` |
| **TEAMSPEAK_PORT** | ServerQuery port (default: 10011) | `10011` |
| **TEAMSPEAK_USER** | ServerQuery username | `mcp_user` |
| **TEAMSPEAK_PASSWORD** | ServerQuery password | `secure_password123` |
| **TEAMSPEAK_SERVER_ID** | Virtual server ID (usually 1) | `1` |

### **🔧 How to Get Your Credentials**

#### **Step 1: Enable ServerQuery**
On your TeamSpeak server, ensure ServerQuery is enabled:
- Check `ts3server.ini`: `query_port=10011`
- Default enabled on most installations

#### **Step 2: Get Admin Access**
- **First installation**: Check server logs for admin token: `token=AAAA...`
- **Existing server**: Use your admin credentials

#### **Step 3: Create MCP User**
Connect to ServerQuery and create a dedicated user:

```bash
# Connect via telnet or putty to your-server:10011
telnet your-server.example.com 10011

# Login with admin
login serveradmin YOUR_ADMIN_PASSWORD

# Create dedicated user for MCP
serverqueryadd client_login_name=mcp_user client_login_password=secure_password123

# Grant necessary permissions (optional - adjust as needed)
servergroupaddclient sgid=6 cldbid=USER_DB_ID
```

#### **Step 4: Test Connection**
```bash
# Test with our connection script
python test_mcp.py

# Or with Docker
docker run --rm -it \
  -e TEAMSPEAK_HOST=your-server.example.com \
  -e TEAMSPEAK_USER=mcp_user \
  -e TEAMSPEAK_PASSWORD=secure_password123 \
  ghcr.io/marlburrow/teamspeak-mcp:latest test
```

### **💡 Quick Configuration Examples**

**For PyPI installation:**
```json
{
  "mcpServers": {
    "teamspeak": {
      "command": "uvx",
      "args": ["teamspeak-mcp", "--host", "your-server.example.com", "--user", "mcp_user", "--password", "secure_password123"]
    }
  }
}
```

**For Docker installation:**
```json
{
  "mcpServers": {
    "teamspeak": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TEAMSPEAK_HOST=your-server.example.com",
        "-e", "TEAMSPEAK_USER=mcp_user",
        "-e", "TEAMSPEAK_PASSWORD=secure_password123",
        "ghcr.io/marlburrow/teamspeak-mcp:latest"
      ]
    }
  }
}
```

> **⚠️ Security Note**: Create a dedicated ServerQuery user with minimal permissions. Never use your admin account for automated tools.

## Usage

Once configured, you can use these commands with Claude:

- *"Connect to TeamSpeak server"*
- *"Send message 'Hello everyone!' to general channel"*
- *"List connected users"*
- *"Create temporary channel called 'Meeting'"*
- *"Move user John to private channel"*
- *"Show me server info"*

## 🛠️ Available Tools

- `connect_to_server` : Connect to TeamSpeak server
- `send_channel_message` : Send message to a channel
- `send_private_message` : Send private message
- `list_clients` : List connected clients
- `list_channels` : List channels
- `create_channel` : Create new channel
- `delete_channel` : Delete channel
- `move_client` : Move client to another channel
- `kick_client` : Kick client
- `ban_client` : Ban client
- `server_info` : Get server information

## 🔧 Development

### Local testing
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python test_mcp.py

# Start MCP server
python -m teamspeak_mcp.server
```

### Docker build
```bash
# Build
docker build -t teamspeak-mcp .

# Test
docker run --rm -it teamspeak-mcp
```

## 🔒 Security

- 🔑 Never commit credentials in code
- 🛡️ Use ServerQuery accounts with limited privileges
- 🌐 Configure firewall to restrict ServerQuery port access
- 🔄 Change ServerQuery passwords regularly

## 🚀 **Automatized Release Workflow (For Maintainers)**

This project uses **fully automated releases** via GitHub Actions. No manual PyPI uploads needed!

### **How it works:**

1. **One Command Release:**
   ```bash
   # Patch release (1.0.3 -> 1.0.4)
   make release-patch
   
   # Minor release (1.0.3 -> 1.1.0) 
   make release-minor
   
   # Major release (1.0.3 -> 2.0.0)
   make release-major
   ```

2. **Automatic Process:**
   - ✅ Bumps version in `pyproject.toml`
   - ✅ Creates git commit and tag
   - ✅ Pushes to GitHub
   - ✅ GitHub Actions triggers automatically:
     - 🔨 Builds Python package
     - 🧪 Tests on TestPyPI first
     - 📦 Publishes to PyPI
     - 🐳 Builds and publishes Docker images
     - 📝 Creates GitHub release with changelog

3. **Setup (One-time):**
   ```bash
   # Show setup instructions
   make setup-pypi
   ```

### **Result:**
- **PyPI**: `uvx install teamspeak-mcp` gets the new version
- **Docker**: `ghcr.io/marlburrow/teamspeak-mcp:v1.0.4` available
- **GitHub**: Automatic release with changelog
- **No manual work needed!** 🎉

## 📦 Release Process

This project uses automated GitHub Actions for building and publishing Docker images:

1. **Tag a release**: `make release-patch` (or `release-minor`/`release-major`)
2. **Automatic build**: GitHub Actions builds and pushes multi-arch images
3. **Available everywhere**: PyPI, GitHub Container Registry, and GitHub Releases

## 🆘 Troubleshooting

### Common Issues

1. **"Connection refused"**
   - Check that ServerQuery is enabled on your server
   - Verify port (default: 10011)

2. **"Authentication failed"**
   - Check your ServerQuery credentials
   - Ensure user has proper permissions

3. **"Virtual server not found"**
   - Check virtual server ID with `serverlist`

4. **"Python version error"**
   - Ensure you're using Python 3.10-3.12
   - The MCP library requires Python 3.10+

5. **"Docker environment variables not working"**
   - Use `-e` flags in args instead of the `"env": {}` field for better compatibility
   - Ensure environment variables are passed correctly in Docker args
   - Check that all required variables are provided: TEAMSPEAK_HOST, TEAMSPEAK_USER, TEAMSPEAK_PASSWORD

### Logs
```bash
# With Docker
docker logs container-name

# Without Docker
python -m teamspeak_mcp.server --verbose
```

## 📝 License

MIT
