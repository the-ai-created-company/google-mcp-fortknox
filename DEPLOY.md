# 🚀 DEPLOYMENT INSTRUCTIONS

## Quick Deploy to Google Cloud

```bash
# Clone the repository
git clone https://github.com/Insta-Bids-System/google-mcp-fortknox.git
cd google-mcp-fortknox

# Make the script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

That's it! The script will handle everything automatically.

## What Gets Deployed

This deployment creates a single enhanced Open WebUI container with:

- **2,953 Google Cloud operations** across 27 services
- **200+ Open WebUI control operations**
- **MCP Factory** for instant tool generation
- **Full self-modification capabilities**

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Build with Cloud Build

```bash
gcloud builds submit --config=cloudbuild.yaml .
```

### 2. Or Build Locally

```bash
# Build the container
docker build -f deployment/Dockerfile -t gcr.io/arched-logic-464602-d9/open-webui-enhanced .

# Push to Container Registry
docker push gcr.io/arched-logic-464602-d9/open-webui-enhanced

# Deploy to Cloud Run
gcloud run deploy open-webui-enhanced \
  --image gcr.io/arched-logic-464602-d9/open-webui-enhanced \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --port 8080 \
  --service-account=mcp-master@arched-logic-464602-d9.iam.gserviceaccount.com
```

## Available Endpoints

Once deployed:

- **Main UI**: `https://YOUR_SERVICE_URL/`
- **MCP Factory**: `https://YOUR_SERVICE_URL/mcp/`
- **List Services**: `https://YOUR_SERVICE_URL/mcp/list_available_services`
- **Health Check**: `https://YOUR_SERVICE_URL/health`

## Testing the Deployment

```bash
# List all available services
curl https://YOUR_SERVICE_URL/mcp/list_available_services

# Create a tool
curl -X POST https://YOUR_SERVICE_URL/mcp/create_google_cloud_tool \
  -H "Content-Type: application/json" \
  -d '{"service": "compute", "operation_id": "instances.list"}'
```

## Prerequisites

- Google Cloud Project with billing enabled
- gcloud CLI installed
- Service account with necessary permissions (script creates if missing)

## Troubleshooting

If deployment fails:

1. Check Cloud Build logs: `gcloud builds list`
2. Check Cloud Run logs: `gcloud run services logs open-webui-enhanced`
3. Verify service account permissions
4. Ensure APIs are enabled

## Architecture

The deployment creates a single container running:

1. **Open WebUI** on port 8080 (main interface)
2. **MCP Factory** on port 8888 (internal, proxied via /mcp/)
3. **Supervisor** managing both processes

All 3,153+ operations are embedded as blueprints for instant access!