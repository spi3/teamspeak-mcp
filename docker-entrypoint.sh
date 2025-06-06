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
        show_config
        check_env
        
        # Optional connection test
        if [ "${SKIP_CONNECTION_TEST:-false}" != "true" ]; then
            test_connection
        fi
        
        log "Launching MCP server..."
        exec python -m teamspeak_mcp.server
        ;;
        
    "test")
        log "🧪 Test mode - Checking configuration..."
        show_config
        check_env
        test_connection
        success "All tests passed!"
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
        echo "  server (default)  - Launch MCP server"
        echo "  test             - Connection tests"
        echo "  shell|bash       - Interactive shell"
        echo "  config           - Display configuration"
        echo "  help             - This help"
        echo ""
        echo "Required environment variables:"
        echo "  TEAMSPEAK_HOST     - TeamSpeak server address"
        echo "  TEAMSPEAK_PASSWORD - ServerQuery password"
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