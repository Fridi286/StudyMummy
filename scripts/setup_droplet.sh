#!/usr/bin/env bash
# ==============================================================================
# StudyMummy - DigitalOcean / Production Droplet Automated Setup Script
# ==============================================================================
# This script prepares a fresh Linux server (e.g., Ubuntu 22.04/24.04 LTS Droplet)
# for running StudyMummy in production with Cloudflare Tunnel HTTPS.
#
# What it does:
# 1. Configures a 2GB Linux Swap file (preventing OOM crashes during docker build on 1GB RAM Droplets).
# 2. Installs Docker & Docker Compose if not already present.
# 3. Creates a starter .env file from .env.example if one doesn't exist.
# ==============================================================================

set -e

echo "🚀 Starting StudyMummy Production Droplet Setup..."
echo "--------------------------------------------------"

# 1. Check and Configure 2GB Swap File (Crucial for 1GB RAM Droplets)
if [ $(swapon --show | wc -l) -le 1 ]; then
    echo "⚠️  No active swap detected. Setting up 2GB Linux swap file to prevent out-of-memory build errors..."
    if [ ! -f /swapfile ]; then
        sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
    fi
    sudo swapon /swapfile
    
    # Make swap permanent across server reboots
    if ! grep -q "/swapfile" /etc/fstab; then
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    echo "✅ 2GB Swap file successfully created and enabled."
else
    echo "✅ Active swap file detected. Skipping swap creation."
fi

echo "--------------------------------------------------"

# 2. Check and Install Docker
if command -v docker >/dev/null 2>&1 || sudo docker --version >/dev/null 2>&1 || [ -f /usr/bin/docker ] || [ -f /snap/bin/docker ] || [ -f /usr/local/bin/docker ]; then
    echo "✅ Docker is already installed."
else
    echo "⚠️  Docker not found. Installing Docker and Docker Compose..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm -f get-docker.sh
    echo "✅ Docker successfully installed."
fi

echo "--------------------------------------------------"

# 3. Prepare Environment Variables File
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Created .env file from .env.example."
        echo "--------------------------------------------------"
        echo "⚠️  ABORTING SETUP: You must edit .env before proceeding!"
        echo "   Please open .env and add your real secrets:"
        echo "   - OPENAI_API_KEY=sk-..."
        echo "   - CLOUDFLARE_TUNNEL_TOKEN=eyJh..."
        echo ""
        echo "   Run: nano .env"
        echo "   After saving your secrets, run this script again or launch Docker Compose!"
        echo "--------------------------------------------------"
        exit 0
    else
        echo "❌ Error: .env.example not found in current directory."
        exit 1
    fi
else
    echo "✅ .env file already exists."
    
    # Check if .env still contains default placeholder secrets
    if grep -q "sk-5678ijklmnopabcd" .env 2>/dev/null || grep -q "CLOUDFLARE_TUNNEL_TOKEN=$" .env 2>/dev/null; then
        echo "--------------------------------------------------"
        echo "⚠️  ABORTING SETUP: Your .env file still contains empty or placeholder secrets!"
        echo "   Please open .env and add your real OPENAI_API_KEY and CLOUDFLARE_TUNNEL_TOKEN."
        echo ""
        echo "   Run: nano .env"
        echo "   Once configured, run this script again or launch Docker Compose!"
        echo "--------------------------------------------------"
        exit 0
    fi
fi

echo "--------------------------------------------------"
echo "🎉 Setup Complete! Your Droplet is ready for production."
echo ""
echo "Next Steps:"
echo "1. Edit your secrets in .env (if you haven't already):"
echo "   nano .env"
echo ""
echo "2. Build and launch StudyMummy in production mode:"
echo "   docker compose --profile prod up -d --build"
echo ""
echo "3. Check container status & logs:"
echo "   docker compose --profile prod ps"
echo "   docker compose --profile prod logs -f cloudflared"
echo "--------------------------------------------------"
