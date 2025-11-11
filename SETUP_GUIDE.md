# Onyx Setup Guide

## Quick Start

This project is **Onyx** - an Open Source AI Platform that provides:
- ✅ Support for any LLM (OpenAI, Claude, Gemini, Ollama, etc.)
- ✅ Smart document search (RAG)
- ✅ Fully self-hosted
- ✅ No GPU required (using cloud APIs)

## Prerequisites

1. **Docker and Docker Compose**
   - Linux: `sudo apt-get install docker.io docker-compose-plugin`
   - macOS: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Windows: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **System Requirements:**
   - RAM: 8GB minimum
   - Disk: 20GB free space
   - CPU: 4 cores recommended

## Installation Steps

### 1. Clone the repository (if you haven't already)

\`\`\`bash
git clone https://github.com/TahaHosseinpour/onyx.git
cd onyx
\`\`\`

### 2. Run the project

#### Option A: Using the quick start script (recommended)

\`\`\`bash
./run.sh
\`\`\`

That's it! The script will:
- Check Docker installation
- Set up environment configuration
- Start all services
- Show you the status

#### Option B: Manual setup

\`\`\`bash
cd deployment/docker_compose

# The .env file is already prepared!
# If you want to customize settings, edit the .env file

# Start all services
docker compose up -d

# View logs
docker compose logs -f
\`\`\`

### 3. Access the application

- Open http://localhost:3000 in your browser
- Wait 2-3 minutes for all services to initialize (first time may take 3-5 minutes)

### 4. Configure LLM Provider

After the application starts:

1. Go to Admin settings: http://localhost:3000/admin/configuration
2. Navigate to the **"LLM Providers"** tab
3. Click **"+ Add Provider"**
4. Enter the following information:

\`\`\`
Provider Name: Metis AI
Provider Type: OpenAI
API Key: tpsg-ATDlOuvhdFEWjHUb4vHf56bU66LwoGi
API Base URL: https://api.metisai.ir/openai/v1
Default Model: gpt-4o
Fast Model: gpt-4o-mini
\`\`\`

5. Save and set as Default

## Useful Commands

### Using the run.sh script

\`\`\`bash
./run.sh start      # Start all services
./run.sh stop       # Stop all services
./run.sh restart    # Restart services
./run.sh logs       # View logs
./run.sh status     # Check service status
./run.sh update     # Update to latest version
./run.sh clean      # Remove all services and data
./run.sh help       # Show help
\`\`\`

### Manual Docker Compose commands

\`\`\`bash
cd deployment/docker_compose

# Start all services
docker compose up -d

# Stop all services
docker compose down

# View service status
docker compose ps

# View logs for a specific service
docker compose logs -f api_server
docker compose logs -f web_server

# Restart a specific service
docker compose restart api_server

# Remove everything (including data)
docker compose down -v
\`\`\`

## System Architecture

The project consists of these services:

- **web_server** (Next.js): User interface - Port 3000
- **api_server** (FastAPI): Backend API - Port 8080
- **background**: Background jobs (Celery)
- **relational_db** (PostgreSQL): Main database - Port 5432
- **index** (Vespa): Search engine - Port 8081, 19071
- **cache** (Redis): Cache - Port 6379
- **minio**: File storage - Port 9000, 9001
- **nginx**: Reverse Proxy - Port 80

## Metis AI Features

This project is configured with **Metis AI** which provides:

- ✅ **No VPN required**: Direct access from Iran
- ✅ **Pay in Rial**: No need for foreign currency
- ✅ **High speed**: Servers close to Iran
- ✅ **OpenAI compatible**: Same API and libraries
- ✅ **Access to latest models**: GPT-4o, GPT-4o-mini, Claude, Gemini, etc.

## Troubleshooting

### Error: Port already in use

\`\`\`bash
# Check what's using port 3000
sudo lsof -i :3000

# Kill the process
sudo kill -9 <PID>
\`\`\`

### Error: Docker daemon not running

\`\`\`bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Open Docker Desktop application
\`\`\`

### Application is slow or crashes

1. Increase Docker resources (Settings → Resources)
2. Allocate at least 8GB RAM and 4 CPUs
3. Check disk space: `docker system df`
4. Clean cache: `docker system prune -a`

### Embedding or LLM not working

1. Check the API key
2. View api_server logs: `docker compose logs -f api_server`
3. Test connection to metisai.ir:
   \`\`\`bash
   curl https://api.metisai.ir/openai/v1/models \\
     -H "Authorization: Bearer YOUR_API_KEY"
   \`\`\`

## Additional Resources

- [Onyx Documentation](https://docs.onyx.app/)
- [Metis AI Setup Guide (Persian)](./METIS_AI_SETUP.md)
- [Onyx GitHub](https://github.com/onyx-dot-app/onyx)
- [Onyx Discord Community](https://discord.gg/TDJ59cGV2X)

## Support

If you encounter any issues, check the logs or ask questions in the Discord community.

Good luck! 🎉
