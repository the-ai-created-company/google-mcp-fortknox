#!/bin/bash
# Local development setup script for Fort Knox

echo "🏗️ Setting up Fort Knox for local development..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "Download from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. It should come with Docker Desktop."
    exit 1
fi

echo "✅ Docker and docker-compose are installed"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p credentials
mkdir -p shared-memory
mkdir -p mcp-tools/generated

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env 2>/dev/null || echo "⚠️  No .env.example found, using defaults"
fi

# Install MCP server dependencies
echo "📦 Installing MCP server dependencies..."
cd mcp-server
npm install
npm run build
cd ..

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add your Google Cloud service account key to: credentials/service-account-key.json"
echo "2. Update the .env file with your configuration"
echo "3. Run: docker-compose up"
echo "4. Access Open WebUI at: http://localhost:8080"
echo "5. MCP Server will be available at: http://localhost:8888"
echo ""
echo "🚀 To start the system: docker-compose up"
echo "🛑 To stop the system: docker-compose down"
echo "📊 To view logs: docker-compose logs -f"
