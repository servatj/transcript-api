#!/bin/bash

# Digital Ocean Deployment Script
set -e

echo "🚀 Deploying Transcript API to Digital Ocean..."

# Create deployment directory
sudo mkdir -p /opt/transcript-api
cd /opt/transcript-api

# Download docker-compose and nginx config
echo "📥 Downloading configuration files..."
curl -o docker-compose.yml https://raw.githubusercontent.com/YOUR_USERNAME/transcript-api/main/docker-compose.prod.yml
curl -o nginx.conf https://raw.githubusercontent.com/YOUR_USERNAME/transcript-api/main/nginx.conf

# Create environment file
echo "⚙️ Setting up environment..."
cat > .env << EOF
DOCKER_USERNAME=${DOCKER_USERNAME}
API_KEY=${API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
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

# Pull and start services
echo "🏁 Starting services..."
docker-compose pull
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