# Onyx Deployment Guide - Cloud API Mode (No GPU Required)

## Overview
This deployment configuration has been modified to use cloud-based APIs instead of local GPU models, making it suitable for deployment on standard servers without GPU hardware.

## Changes Made

### 1. Embedding Model
- **Before**: `nomic-ai/nomic-embed-text-v1` (local, GPU-based)
- **After**: `openai/text-embedding-3-small` (cloud API)
- **Dimension**: 1536 (updated from 768)

### 2. Model Servers
- Both `inference_model_server` and `indexing_model_server` have been disabled
- All model inference now uses cloud APIs (OpenAI, Cohere, etc.)

### 3. Docker Compose
- Model server services commented out
- `DISABLE_MODEL_SERVER=True` set for all backend services
- Dependencies on model servers removed

## Prerequisites

1. **Docker & Docker Compose** installed
2. **OpenAI API Key** (required for embeddings)
3. **Optional**: Cohere API key for better reranking

## Quick Start

### Step 1: Configure Environment

Edit the `.env` file in this directory:

```bash
# REQUIRED: Set your OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Embedding configuration (already set)
DOCUMENT_ENCODER_MODEL=openai/text-embedding-3-small
DOC_EMBEDDING_DIM=1536
DISABLE_MODEL_SERVER=true

# Optional: Set authentication
AUTH_TYPE=basic  # or google_oauth, oidc, saml
```

### Step 2: Start the Application

```bash
cd deployment/docker_compose
docker compose up -d
```

### Step 3: Access the Application

- **Web Interface**: http://localhost:3000
- **API Server**: http://localhost:8080

## Configuration Options

### Authentication

#### Basic Authentication (Username/Password)
```bash
AUTH_TYPE=basic
```

#### Google OAuth
```bash
AUTH_TYPE=google_oauth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
SECRET=your-random-secret-key
```

#### OIDC
```bash
AUTH_TYPE=oidc
OPENID_CONFIG_URL=https://your-idp.com/.well-known/openid-configuration
```

#### SAML
```bash
AUTH_TYPE=saml
SAML_CONF_DIR=/path/to/saml/config
```

### Embedding Providers

You can switch to different embedding providers:

#### OpenAI (Default)
```bash
DOCUMENT_ENCODER_MODEL=openai/text-embedding-3-small
DOC_EMBEDDING_DIM=1536
```

#### Cohere
```bash
DOCUMENT_ENCODER_MODEL=cohere/embed-english-v3.0
DOC_EMBEDDING_DIM=1024
```

#### Google Gemini
```bash
DOCUMENT_ENCODER_MODEL=google/gemini-embedding-001
DOC_EMBEDDING_DIM=3072
```

### Reranking Configuration

For better search results, enable reranking with Cohere:

```bash
DEFAULT_CROSS_ENCODER_PROVIDER_TYPE=cohere
DEFAULT_CROSS_ENCODER_API_KEY=your-cohere-api-key
```

### LLM Configuration

Configure your LLM through the UI after deployment, or set via environment:

```bash
GEN_AI_API_KEY=your-openai-api-key
GEN_AI_MODEL_VERSION=gpt-4
FAST_GEN_AI_MODEL_VERSION=gpt-3.5-turbo
```

## Production Deployment Checklist

### 1. Security
- [ ] Set strong passwords for `POSTGRES_PASSWORD` and `MINIO_ROOT_PASSWORD`
- [ ] Enable authentication (`AUTH_TYPE`)
- [ ] Set `ENCRYPTION_KEY_SECRET` for secure session encryption
- [ ] Remove port exposures except nginx (80/443)
- [ ] Configure SSL/TLS certificates

### 2. Database
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong-random-password-here
```

### 3. S3/MinIO
```bash
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=strong-random-password-here
S3_AWS_ACCESS_KEY_ID=admin
S3_AWS_SECRET_ACCESS_KEY=strong-random-password-here
```

### 4. Domain & SSL

Edit `docker-compose.yml` nginx section:
```yaml
environment:
  - DOMAIN=yourdomain.com
```

Uncomment SSL volumes:
```yaml
volumes:
  - ../data/certbot/conf:/etc/letsencrypt
  - ../data/certbot/www:/var/www/certbot
```

Change nginx command to use production template:
```yaml
command: >
  /bin/sh -c "dos2unix /etc/nginx/conf.d/run-nginx.sh
  && /etc/nginx/conf.d/run-nginx.sh app.conf.template.prod"
```

### 5. Email Configuration (for user verification)

```bash
REQUIRE_EMAIL_VERIFICATION=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASS=your-app-password
EMAIL_FROM=noreply@yourdomain.com
```

## Monitoring & Maintenance

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api_server
docker compose logs -f background
```

### Restart Services
```bash
# All services
docker compose restart

# Specific service
docker compose restart api_server
```

### Update to Latest Version
```bash
docker compose pull
docker compose up -d
```

### Backup Database
```bash
docker compose exec relational_db pg_dump -U postgres postgres > backup.sql
```

### Restore Database
```bash
docker compose exec -T relational_db psql -U postgres postgres < backup.sql
```

## Scaling Considerations

### Horizontal Scaling
To scale the API server:
```bash
docker compose up -d --scale api_server=3
```

### Database Connection Pooling
Adjust in `.env`:
```bash
POSTGRES_API_SERVER_POOL_SIZE=60
POSTGRES_API_SERVER_POOL_OVERFLOW=10
```

### Worker Concurrency
```bash
CELERY_WORKER_DOCFETCHING_CONCURRENCY=4
CELERY_WORKER_DOCPROCESSING_CONCURRENCY=4
```

## Cost Optimization

### Embedding Costs
- OpenAI `text-embedding-3-small`: ~$0.02 per 1M tokens
- OpenAI `text-embedding-3-large`: ~$0.13 per 1M tokens
- Cohere `embed-english-v3.0`: ~$0.10 per 1M tokens

**Recommendation**: Use `text-embedding-3-small` for cost-effectiveness

### LLM Costs
Configure via UI with cost-aware model selection:
- Fast model: `gpt-3.5-turbo` (cheaper for simple queries)
- Advanced model: `gpt-4` (better quality for complex queries)

## Troubleshooting

### Issue: Services won't start
**Solution**: Check logs and ensure all required environment variables are set
```bash
docker compose logs api_server
```

### Issue: Embedding errors
**Solution**: Verify `OPENAI_API_KEY` is set correctly
```bash
docker compose exec api_server printenv | grep OPENAI_API_KEY
```

### Issue: Database connection errors
**Solution**: Wait for database to be ready
```bash
docker compose logs relational_db
docker compose restart api_server
```

### Issue: Out of memory
**Solution**: Increase Docker memory limit or use a larger instance

### Issue: Slow performance
**Solution**:
1. Enable reranking with Cohere
2. Increase worker concurrency
3. Use faster embedding models

## Migration from GPU Version

If migrating from a GPU-based deployment:

1. **Backup your data**:
   ```bash
   docker compose exec relational_db pg_dump -U postgres postgres > backup.sql
   ```

2. **Re-index documents**: After switching to cloud embeddings, you need to re-index all documents because embedding dimensions changed from 768 to 1536.

3. **Update Vespa schema**: The dimension change requires Vespa schema update (handled automatically on first run)

## Support & Documentation

- **Official Docs**: https://docs.onyx.app
- **GitHub**: https://github.com/onyx-dot-app/onyx
- **Discord**: Join the Onyx community

## API Keys Setup Guide

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Cohere API Key (Optional)
1. Go to https://dashboard.cohere.com/api-keys
2. Create a new API key
3. Add to `.env`: `DEFAULT_CROSS_ENCODER_API_KEY=...`

### Google OAuth (Optional)
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add authorized redirect URIs: `http://localhost:3000/api/auth/callback/google`
4. Add credentials to `.env`

## Performance Benchmarks

### Cloud API Mode (This Configuration)
- **Hardware**: Any server with 4GB+ RAM, 2+ CPU cores
- **Cost**: Pay-per-use based on API calls
- **Latency**: 100-500ms per embedding request
- **Scalability**: Excellent (scales with API limits)

### GPU Mode (Original)
- **Hardware**: NVIDIA GPU with 8GB+ VRAM
- **Cost**: Fixed hardware cost
- **Latency**: 10-50ms per embedding request
- **Scalability**: Limited by GPU memory

## Next Steps

1. ✅ Configure `.env` with your API keys
2. ✅ Start the application: `docker compose up -d`
3. ✅ Access http://localhost:3000
4. ✅ Configure LLM settings in the UI (Admin → Settings)
5. ✅ Add your first data connector
6. ✅ Start chatting!

---

**Note**: This configuration is production-ready for cloud deployment without GPU requirements. For high-volume deployments (>1M documents), consider using GPU-based deployment or enterprise features.
