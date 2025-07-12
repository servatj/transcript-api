#!/bin/bash

# Digital Ocean Deployment with GitHub Container Registry
set -e

echo "🚀 Deploying Transcript API to Digital Ocean (GitHub Container Registry)..."

# Create deployment directory
sudo mkdir -p /opt/transcript-api
cd /opt/transcript-api

# Install Git if not present
if ! command -v git &> /dev/null; then
    echo "📦 Installing Git..."
    sudo apt update
    sudo apt install -y git
fi

# Clone or update repository (for docker-compose.yml and .env setup)
if [ -d ".git" ]; then
    echo "📥 Updating repository..."
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone https://github.com/$GITHUB_REPOSITORY.git .
fi

# Create environment file
echo "⚙️ Setting up environment..."
cat > .env << EOF
API_KEY=${API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
REDIS_HOST=redis
REDIS_PORT=6379
EOF

# Install Docker and Docker Compose if not already installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Login to GitHub Container Registry (public images don't require auth, but good practice)
echo "🔐 Logging into GitHub Container Registry..."
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin 2>/dev/null || echo "Note: GHCR login failed, assuming public image"

# Pull latest image and start services
echo "🏗️ Pulling latest image and starting services..."
docker-compose down || true
docker pull ${IMAGE_TAG} || echo "Pull failed, will use cached image"
docker-compose up -d

# Setup UFW firewall
echo "🔒 Setting up firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

echo "✅ Deployment complete!"
echo "🌐 Your API should be available at: http://$(curl -s ifconfig.me)"
echo "📚 API Documentation: http://$(curl -s ifconfig.me)/docs"