#!/bin/bash
# Deploy Enhanced Open WebUI to Google Cloud Run
# This script builds and deploys the complete infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-arched-logic-464602-d9}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="open-webui-enhanced"
SERVICE_ACCOUNT="mcp-master@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${GREEN}🚀 Enhanced Open WebUI Deployment Script${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check authentication
echo -e "\n${YELLOW}📋 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Not authenticated. Running gcloud auth login...${NC}"
    gcloud auth login
fi

# Set project
echo -e "\n${YELLOW}📋 Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "\n${YELLOW}📋 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com

# Check if service account exists
echo -e "\n${YELLOW}📋 Checking service account...${NC}"
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT} &> /dev/null; then
    echo -e "${RED}❌ Service account ${SERVICE_ACCOUNT} not found.${NC}"
    echo -e "${YELLOW}Creating service account...${NC}"
    gcloud iam service-accounts create mcp-master \
        --display-name="MCP Master Service Account"
fi

# Build the container using Cloud Build
echo -e "\n${YELLOW}🏗️  Building enhanced container with Cloud Build...${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  • 2,953 Google Cloud operations"
echo -e "  • 200+ Open WebUI control operations"
echo -e "  • MCP Factory for dynamic tool generation"

# Submit the build
if gcloud builds submit --config=cloudbuild.yaml .; then
    echo -e "${GREEN}✅ Build and deployment completed successfully!${NC}"
else
    echo -e "${RED}❌ Build failed. Check Cloud Build logs for details.${NC}"
    exit 1
fi

# Get the service URL
echo -e "\n${YELLOW}📋 Getting service information...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --format="value(status.url)")

if [ -n "$SERVICE_URL" ]; then
    echo -e "\n${GREEN}🎉 Deployment Successful!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Service URL:${NC} ${SERVICE_URL}"
    echo -e "${GREEN}MCP Factory:${NC} ${SERVICE_URL}/mcp/"
    echo -e "\n${YELLOW}Available endpoints:${NC}"
    echo -e "  • Main UI: ${SERVICE_URL}"
    echo -e "  • MCP Factory: ${SERVICE_URL}/mcp/list_available_services"
    echo -e "  • Health Check: ${SERVICE_URL}/health"
    echo -e "\n${YELLOW}Total operations available:${NC}"
    echo -e "  • Google Cloud: 2,953 operations"
    echo -e "  • Open WebUI: 200+ operations"
    echo -e "  • Total: 3,153+ operations"
else
    echo -e "${RED}❌ Failed to get service URL. Check Cloud Run console.${NC}"
fi

echo -e "\n${GREEN}✨ Your autonomous AI infrastructure is ready!${NC}"