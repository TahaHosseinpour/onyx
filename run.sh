#!/bin/bash

# Script to easily run Onyx project
# Created by Claude

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
echo ""
echo "╔═══════════════════════════════════════╗"
echo "║     Onyx - Open Source AI Platform   ║"
echo "║        Quick Setup Script             ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check if Docker is installed
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo ""
    echo "Please install Docker first:"
    echo "  - Linux:   sudo apt-get install docker.io docker-compose-plugin"
    echo "  - macOS:   Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    echo "  - Windows: Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    echo ""
    exit 1
fi
print_success "Docker is installed"

# Check if Docker daemon is running
print_info "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running!"
    echo ""
    echo "Please start Docker:"
    echo "  - Linux:   sudo systemctl start docker"
    echo "  - macOS/Windows: Start Docker Desktop application"
    echo ""
    exit 1
fi
print_success "Docker daemon is running"

# Check if Docker Compose is available
print_info "Checking Docker Compose..."
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    print_success "Docker Compose is available"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    print_success "Docker Compose (standalone) is available"
else
    print_error "Docker Compose is not installed!"
    echo ""
    echo "Please install Docker Compose plugin:"
    echo "  sudo apt-get install docker-compose-plugin"
    echo ""
    exit 1
fi

# Navigate to docker compose directory
cd "$(dirname "$0")/deployment/docker_compose"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found, copying from .env.metis-example..."
    cp .env.metis-example .env
    print_success ".env file created"
else
    print_success ".env file exists"
fi

echo ""
print_info "Starting Onyx services..."
echo ""

# Function to handle different commands
case "${1:-start}" in
    start|up)
        print_info "Pulling latest images (if needed)..."
        $COMPOSE_CMD pull

        print_info "Starting all services..."
        $COMPOSE_CMD up -d

        echo ""
        print_success "Onyx is starting up!"
        echo ""
        echo "Services:"
        $COMPOSE_CMD ps
        echo ""
        print_info "Please wait 2-3 minutes for all services to be ready..."
        print_info "You can check logs with: $COMPOSE_CMD logs -f"
        echo ""
        print_success "Access Onyx at: ${GREEN}http://localhost:3000${NC}"
        echo ""
        ;;

    stop|down)
        print_info "Stopping all services..."
        $COMPOSE_CMD down
        print_success "All services stopped"
        ;;

    restart)
        print_info "Restarting all services..."
        $COMPOSE_CMD restart
        print_success "All services restarted"
        ;;

    logs)
        print_info "Showing logs (Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f
        ;;

    status|ps)
        echo ""
        print_info "Service status:"
        $COMPOSE_CMD ps
        echo ""
        ;;

    clean)
        print_warning "This will remove all containers and data!"
        read -p "Are you sure? (yes/no): " -n 3 -r
        echo
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            print_info "Removing all services and data..."
            $COMPOSE_CMD down -v
            print_success "Cleanup complete"
        else
            print_info "Cleanup cancelled"
        fi
        ;;

    update)
        print_info "Updating to latest version..."
        $COMPOSE_CMD pull
        $COMPOSE_CMD down
        $COMPOSE_CMD up -d
        print_success "Update complete"
        ;;

    help|--help|-h)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start, up    - Start all services (default)"
        echo "  stop, down   - Stop all services"
        echo "  restart      - Restart all services"
        echo "  logs         - Show logs (follow mode)"
        echo "  status, ps   - Show service status"
        echo "  update       - Update to latest version"
        echo "  clean        - Remove all services and data"
        echo "  help         - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0              # Start Onyx"
        echo "  $0 start        # Start Onyx"
        echo "  $0 logs         # View logs"
        echo "  $0 stop         # Stop Onyx"
        echo ""
        ;;

    *)
        print_error "Unknown command: $1"
        echo ""
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

echo ""
