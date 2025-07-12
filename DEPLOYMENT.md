# 🚀 Digital Ocean Deployment Guide

## Required Droplet Specifications

### Recommended Droplet:
- **Size**: 2 GB RAM / 1 vCPU / 50 GB SSD (**$12/month**)
- **OS**: Ubuntu 22.04 LTS
- **Region**: Choose closest to your users
- **Additional**: Enable monitoring

### Why this size?
- **FastAPI**: ~200-300MB RAM
- **Redis**: ~50-100MB RAM  
- **yt-dlp**: ~100-200MB RAM during processing
- **System**: ~500MB RAM
- **Buffer**: ~1GB for peaks and OS

## Setup Steps

### 1. Create Digital Ocean Droplet
```bash
# Through DO Dashboard or CLI
doctl compute droplet create transcript-api \
  --size s-1vcpu-2gb \
  --image ubuntu-22-04-x64 \
  --region nyc1 \
  --ssh-keys YOUR_SSH_KEY_ID
```

### 2. Configure GitHub Secrets
Add these secrets to your GitHub repository:

```
DO_HOST=your_droplet_ip
DO_USERNAME=root
DO_SSH_KEY=your_private_ssh_key
API_KEY=your_secure_api_key
OPENAI_API_KEY=optional_openai_key
```

**Note**: Docker credentials are no longer needed as we use GitHub Container Registry (GHCR) which uses the built-in `GITHUB_TOKEN`.

### 3. Manual Deployment (One-time)
SSH into your droplet and run:

```bash
# Download and run deployment script
curl -o deploy-simple.sh https://raw.githubusercontent.com/YOUR_USERNAME/transcript-api/main/deploy-simple.sh
chmod +x deploy-simple.sh

# Set environment variables
export API_KEY=your_secure_api_key
export OPENAI_API_KEY=your_openai_key  # optional
export GITHUB_REPOSITORY=your_username/transcript-api
export IMAGE_TAG=ghcr.io/your_username/transcript-api:latest

# Run deployment
./deploy-simple.sh
```

### 4. GitHub Actions Auto-Deploy
After manual setup, every push to `main` branch will:
1. **Build** Docker image and push to GitHub Container Registry (GHCR)
2. **Deploy** by pulling the new image to Digital Ocean and restarting services

The workflow uses GitHub Container Registry at `ghcr.io/your_username/transcript-api:latest`.

## Testing Deployment

```bash
# Health check
curl http://YOUR_DROPLET_IP/

# API documentation
curl http://YOUR_DROPLET_IP/docs

# Test transcript endpoint
curl -X POST "http://YOUR_DROPLET_IP/api/v1/transcript" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "provider": "youtube",
    "video_url": "https://www.youtube.com/watch?v=hTfprtjjKuE"
  }'
```

## Monitoring

```bash
# Check logs
docker-compose logs -f api

# Check status
docker-compose ps

# Resource usage
htop
```

## Cost Estimate
- **Droplet**: $12/month
- **Bandwidth**: Usually included (1TB)
- **Backups**: +$2.40/month (optional)
- **Total**: ~$12-15/month

## Security Features
- ✅ Rate limiting (10 req/s)
- ✅ API key authentication
- ✅ Firewall configured
- ✅ Security headers
- ✅ Redis not exposed publicly

## Scaling Options
If you need more capacity:
- **4GB/2vCPU** ($24/month) - Handle more concurrent requests
- **8GB/4vCPU** ($48/month) - High traffic
- **Load Balancer** - Multiple droplets behind LB