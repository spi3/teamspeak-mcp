# TeamSpeak MCP

A Model Context Protocol (MCP) server for controlling TeamSpeak from AI models like Claude.

## Requirements

- **Python 3.10+** (required by Model Context Protocol SDK)
- **Docker** (optional, for containerized deployment)
- **TeamSpeak 3 Server** with ServerQuery enabled

## Features

- 🎯 Connect to TeamSpeak servers
- 💬 Send messages to channels and private messages
- 📋 List connected users
- 🔧 Channel management (create, delete, move users)
- 🎵 Voice control (mute, unmute, kick, ban)
- 📊 Server statistics

## 🚀 Quick Start with Pre-built Images

We provide pre-built Docker images via GitHub Container Registry for easy deployment:

### Using Latest Release

```bash
# Pull the latest stable release
docker pull ghcr.io/marlburrow/teamspeak-mcp:latest

# Run with environment variables
docker run --rm -i \
  -e TEAMSPEAK_HOST=your-server.example.com \
  -e TEAMSPEAK_PASSWORD=your-password \
  ghcr.io/marlburrow/teamspeak-mcp:latest
```

### Using Specific Version

```bash
# Use a specific version (recommended for production)
docker pull ghcr.io/marlburrow/teamspeak-mcp:v1.0.0

# With docker-compose (update docker-compose.yml)
services:
  teamspeak-mcp:
    image: ghcr.io/marlburrow/teamspeak-mcp:v1.0.0
    # ... rest of your configuration
```

### Available Tags

- `latest` - Latest stable release
- `v1.0.0`, `v1.0`, `v1` - Semantic versioning tags
- `main` - Latest development build

## Installation

### 🐳 Docker Method (Recommended)

1. Clone this repository:
```bash
git clone https://github.com/MarlBurroW/teamspeak-mcp.git
cd teamspeak-mcp
```

2. Configure your credentials in `docker-compose.yml` or create a `.env` file

3. Start with Docker Compose:
```bash
docker-compose up -d
```

### 🐍 Local Python Installation

**Prerequisites**: Python 3.10 or higher

1. Clone this repository:
```bash
git clone https://github.com/MarlBurroW/teamspeak-mcp.git
cd teamspeak-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your TeamSpeak credentials (see next section)

## 🔑 TeamSpeak Credentials Configuration

### Where to find connection information?

#### 1. **Server Address (TEAMSPEAK_HOST)**
- Your public IP address or domain name
- Example: `my-server.com` or `192.168.1.100`

#### 2. **ServerQuery Port (TEAMSPEAK_PORT)**
- Default: `10011`
- Check your TeamSpeak server configuration

#### 3. **ServerQuery Credentials (TEAMSPEAK_USER / TEAMSPEAK_PASSWORD)**

**On your TeamSpeak server:**

1. **Connect as admin** to your TeamSpeak server
2. **Enable ServerQuery** if not done:
   - Go to `Tools` → `ServerQuery Login`
   - Or check `ts3server.ini` file: `query_port=10011`

3. **Create a ServerQuery user**:
   - Connect via telnet/putty to `your-server:10011`
   - Use these commands:
   ```
   # Initial connection (use admin token)
   auth apikey=YOUR_API_KEY
   
   # Or with default serveradmin account
   login serveradmin YOUR_ADMIN_PASSWORD
   
   # Create new user for MCP
   serverqueryadd client_login_name=mcp_user client_login_password=your_password
   ```

4. **Get initial token** (first installation):
   - In TeamSpeak server logs at startup
   - Look for: `token=` in logs

#### 4. **Virtual Server ID (TEAMSPEAK_SERVER_ID)**
- Usually `1` for main server
- Use `serverlist` command via ServerQuery to see all servers

### Configuration Example

Create a `.env` file:
```bash
# TeamSpeak MCP Configuration
TEAMSPEAK_HOST=my-server.teamspeak.com
TEAMSPEAK_PORT=10011
TEAMSPEAK_USER=mcp_user
TEAMSPEAK_PASSWORD=my_secure_password
TEAMSPEAK_SERVER_ID=1
```

## Claude Desktop Configuration

### 🐳 With Pre-built Docker Image

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "teamspeak": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/path/to/your/.env",
        "ghcr.io/marlburrow/teamspeak-mcp:latest"
      ]
    }
  }
}
```

### 🐳 With Local Docker Build

```json
{
  "mcpServers": {
    "teamspeak": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/path/to/your/.env",
        "teamspeak-mcp:latest"
      ]
    }
  }
}
```

### 🐍 Without Docker

```json
{
  "mcpServers": {
    "teamspeak": {
      "command": "python",
      "args": ["-m", "teamspeak_mcp.server"],
      "env": {
        "TEAMSPEAK_HOST": "your-server.example.com",
        "TEAMSPEAK_PORT": "10011",
        "TEAMSPEAK_USER": "serveradmin",
        "TEAMSPEAK_PASSWORD": "your-password",
        "TEAMSPEAK_SERVER_ID": "1"
      }
    }
  }
}
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
docker run --rm -it --env-file .env teamspeak-mcp python test_mcp.py
```

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

## 📦 Release Process

This project uses automated GitHub Actions for building and publishing Docker images:

1. **Tag a release**: `git tag v1.0.0 && git push origin v1.0.0`
2. **Automatic build**: GitHub Actions builds and pushes multi-arch images
3. **Available images**: Images are published to `ghcr.io/marlburrow/teamspeak-mcp`

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
   - Ensure you're using Python 3.10 or higher
   - The MCP library requires Python 3.10+

### Logs
```bash
# With Docker
docker logs container-name

# Without Docker
python -m teamspeak_mcp.server --verbose
```

## 📝 License

MIT 