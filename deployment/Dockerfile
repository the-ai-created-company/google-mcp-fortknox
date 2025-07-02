# Multi-stage build for Enhanced Open WebUI with embedded Google Cloud blueprints
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy all blueprints and components
WORKDIR /build
COPY extracted-data /build/blueprints/
COPY openwebui-control /build/openwebui-control/
COPY mcp-server /build/mcp-server/

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.7 \
    uvicorn[standard]==0.34.2 \
    pydantic==2.10.6 \
    python-multipart==0.0.20 \
    fastmcp \
    google-cloud-storage==2.19.0 \
    google-auth==2.17.3 \
    google-auth-httplib2 \
    google-api-python-client \
    redis \
    aiofiles

# Final stage - build on top of Open WebUI
FROM ghcr.io/open-webui/open-webui:main

# Install supervisor and additional dependencies
RUN apt-get update && apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/*

# Copy blueprints and MCP components from builder
COPY --from=builder /build/blueprints /app/blueprints
COPY --from=builder /build/openwebui-control /app/openwebui-control
COPY --from=builder /build/mcp-server /app/mcp-server

# Copy deployment configurations
COPY deployment/supervisord.conf /etc/supervisor/conf.d/
COPY deployment/mcp_factory.py /app/mcp-factory/

# Install production dependencies
RUN pip install --no-cache-dir \
    fastmcp \
    google-cloud-storage==2.19.0 \
    google-auth==2.17.3 \
    google-auth-httplib2 \
    google-api-python-client

# Environment variables
ENV GOOGLE_CLOUD_PROJECT=arched-logic-464602-d9 \
    ENABLE_MCP_FACTORY=true \
    BLUEPRINTS_PATH=/app/blueprints \
    PYTHONPATH=/app:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 8888

# Start everything with supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]