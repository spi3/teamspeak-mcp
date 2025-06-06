#!/bin/bash
set -e

# Docker entrypoint script for TeamSpeak MCP
# Allows different execution modes

# Colors for logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Debug function to show all environment variables
debug_env() {
    log "🔍 Environment Variables Debug:"
    echo "All TEAMSPEAK_* variables:"
    env | grep "^TEAMSPEAK_" | while read -r line; do
        key=$(echo "$line" | cut -d'=' -f1)
        if [[ "$key" == "TEAMSPEAK_PASSWORD" ]]; then
            echo "  $key=[REDACTED]"
        else
            echo "  $line"
        fi
    done
    echo ""
    echo "All environment variables count: $(env | wc -l)"
    echo "Docker-related variables:"
    env | grep -E "^(PATH|HOME|USER|HOSTNAME)" | head -5
}

# Check required environment variables
check_env() {
    log "Checking configuration..."
    
    if [ -z "$TEAMSPEAK_HOST" ]; then
        error "TEAMSPEAK_HOST is required"
        exit 1
    fi
    
    if [ -z "$TEAMSPEAK_PASSWORD" ]; then
        error "TEAMSPEAK_PASSWORD is required"
        exit 1
    fi
    
    success "Configuration validated"
}

# Test TeamSpeak connection
test_connection() {
    log "Testing TeamSpeak server connection..."
    
    if python test_mcp.py; then
        success "TeamSpeak connection successful"
    else
        error "TeamSpeak connection failed"
        exit 1
    fi
}

# Display configuration (without secrets)
show_config() {
    log "TeamSpeak MCP Configuration:"
    echo "  Host: $TEAMSPEAK_HOST"
    echo "  Port: ${TEAMSPEAK_PORT:-10011}"
    echo "  User: ${TEAMSPEAK_USER:-serveradmin}"
    echo "  Server ID: ${TEAMSPEAK_SERVER_ID:-1}"
    echo "  Password: [REDACTED]"
}

# Main mode handler
case "${1:-server}" in
    "server")
        log "🚀 Starting TeamSpeak MCP server..."
        debug_env
        show_config
        check_env
        
        # Optional connection test
        if [ "${SKIP_CONNECTION_TEST:-false}" != "true" ]; then
            test_connection
        fi
        
        log "Launching MCP server..."
        exec python -m teamspeak_mcp.server
        ;;
        
    "server-cli")
        log "🚀 Starting TeamSpeak MCP server with CLI args..."
        # Pass all arguments except the first one to the Python server
        shift
        exec python -m teamspeak_mcp.server "$@"
        ;;
        
    "test")
        log "🧪 Test mode - Checking configuration..."
        show_config
        check_env
        test_connection
        success "All tests passed!"
        ;;
        
    "debug")
        log "🔍 Debug mode - Full environment analysis..."
        debug_env
        show_config
        echo ""
        echo "Current working directory: $(pwd)"
        echo "Python version: $(python --version)"
        echo "Available Python packages:"
        pip list | grep -E "(mcp|ts3|pydantic)" || echo "  No relevant packages found"
        ;;
        
    "shell"|"bash")
        log "🐚 Shell mode - Opening interactive shell..."
        exec /bin/bash
        ;;
        
    "config")
        log "⚙️ Displaying configuration:"
        show_config
        ;;
        
    "help"|"--help"|"-h")
        echo "TeamSpeak MCP Docker - Available modes:"
        echo ""
        echo "  server (default)  - Launch MCP server with env vars"
        echo "  server-cli        - Launch MCP server with CLI args"
        echo "  test             - Connection tests"
        echo "  debug            - Full environment analysis"
        echo "  shell|bash       - Interactive shell"
        echo "  config           - Display configuration"
        echo "  help             - This help"
        echo ""
        echo "Required environment variables (server mode):"
        echo "  TEAMSPEAK_HOST     - TeamSpeak server address"
        echo "  TEAMSPEAK_PASSWORD - ServerQuery password"
        echo ""
        echo "CLI arguments (server-cli mode):"
        echo "  --host HOST        - TeamSpeak server address"
        echo "  --port PORT        - ServerQuery port (default: 10011)"
        echo "  --user USER        - ServerQuery user (default: serveradmin)"
        echo "  --password PASS    - ServerQuery password"
        echo "  --server-id ID     - Virtual server ID (default: 1)"
        echo ""
        echo "Optional variables:"
        echo "  TEAMSPEAK_PORT     - ServerQuery port (default: 10011)"
        echo "  TEAMSPEAK_USER     - ServerQuery user (default: serveradmin)"
        echo "  TEAMSPEAK_SERVER_ID - Virtual server ID (default: 1)"
        echo "  SKIP_CONNECTION_TEST - Skip connection tests (default: false)"
        ;;
        
    *)
        # If command doesn't match any mode, execute it directly
        log "🔧 Executing custom command: $*"
        exec "$@"
        ;;
esac 