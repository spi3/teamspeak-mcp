#!/bin/bash

# Script de tests d'intégration TeamSpeak MCP
set -e

# Couleurs pour les logs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

header() {
    echo -e "\n${BLUE}🚀 $1${NC}"
    echo "========================================"
}

cleanup() {
    header "Cleaning up containers..."
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
}

main() {
    header "TeamSpeak MCP Integration Tests"
    
    # Vérifier les prérequis
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    success "Docker and Docker Compose are available"
    
    # Créer les dossiers nécessaires
    mkdir -p tests test_results scripts
    
    # Nettoyage initial
    cleanup
    
    # Construire les images
    header "Building Docker images..."
    if docker-compose -f docker-compose.test.yml build; then
        success "Images built successfully"
    else
        error "Failed to build images"
        exit 1
    fi
    
    # Démarrer TeamSpeak 3 Server
    header "Starting TeamSpeak 3 Server..."
    docker-compose -f docker-compose.test.yml up -d teamspeak3-server
    
    # Attendre que TS3 soit prêt
    info "Waiting for TeamSpeak server to be ready..."
    for i in {1..120}; do
        if docker-compose -f docker-compose.test.yml exec -T teamspeak3-server nc -z localhost 10011 2>/dev/null; then
            success "TeamSpeak server is ready after ${i}s"
            break
        fi
        if [ $i -eq 120 ]; then
            error "TeamSpeak server failed to start after 120s"
            docker-compose -f docker-compose.test.yml logs teamspeak3-server
            cleanup
            exit 1
        fi
        sleep 1
    done
    
    # Extraire le token admin
    header "Extracting admin token..."
    docker-compose -f docker-compose.test.yml up token-extractor
    
    if [ -f scripts/admin_token.txt ]; then
        TOKEN=$(cat scripts/admin_token.txt)
        if [ ! -z "$TOKEN" ]; then
            success "Admin token extracted: ${TOKEN:0:10}..."
            # Mettre à jour la variable d'environnement pour les tests
            export TEAMSPEAK_PASSWORD="$TOKEN"
        else
            warning "Empty admin token, will try without password"
        fi
    else
        warning "No admin token file found, will try without password"
    fi
    
    # Lancer les tests d'intégration
    header "Running integration tests..."
    
    # Exporter les variables pour docker-compose
    export TEAMSPEAK_HOST=teamspeak3-server
    export TEAMSPEAK_PORT=10011
    export TEAMSPEAK_USER=serveradmin
    export TEAMSPEAK_SERVER_ID=1
    
    if docker-compose -f docker-compose.test.yml run --rm teamspeak-mcp-test python tests/test_integration.py; then
        success "Integration tests completed successfully!"
        
        # Afficher les résultats si disponibles
        if [ -f test_results/integration_results.json ]; then
            header "Test Results Summary"
            if command -v jq &> /dev/null; then
                echo "📊 Detailed results:"
                cat test_results/integration_results.json | jq '.[] | "\(.tool): \(.status) - \(.message)"' -r
            else
                info "Install 'jq' to see detailed test results"
                info "Results saved in test_results/integration_results.json"
            fi
        fi
        
        TEST_EXIT_CODE=0
    else
        error "Integration tests failed!"
        
        # Afficher les logs en cas d'erreur
        header "Container logs for debugging:"
        echo "TeamSpeak server logs:"
        docker-compose -f docker-compose.test.yml logs --tail=50 teamspeak3-server
        echo -e "\nMCP test logs:"
        docker-compose -f docker-compose.test.yml logs --tail=50 teamspeak-mcp-test
        
        TEST_EXIT_CODE=1
    fi
    
    # Nettoyage final
    cleanup
    
    # Message final
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        success "🎉 All integration tests passed!"
        info "Results are available in test_results/"
    else
        error "💥 Some integration tests failed!"
        info "Check the logs above for details"
    fi
    
    exit $TEST_EXIT_CODE
}

# Gestion des signaux pour nettoyage
trap cleanup EXIT
trap cleanup INT
trap cleanup TERM

# Exécution du script principal
main "$@" 