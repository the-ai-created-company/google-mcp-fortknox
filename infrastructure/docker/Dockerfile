# Production Multi-Stage Dockerfile for Autonomous AI Platform
# This creates a single container with Open WebUI + MCP Factory + All Tools

# Stage 1: Build the MCP tools
FROM node:20-alpine AS mcp-builder

WORKDIR /build

# Copy existing MCP tools from Fort Knox
COPY mcp-server/ ./mcp-server/
COPY extracted-data/ ./blueprints/

# Install dependencies and build
RUN cd mcp-server && npm install && npm run build

# Stage 2: Python dependencies
FROM python:3.11-slim AS python-builder

WORKDIR /build

# Copy requirements and install dependencies
COPY infrastructure/docker/requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Final production image
FROM ghcr.io/open-webui/open-webui:main

# Metadata
LABEL maintainer="InstaBids System <instabidssystem@gmail.com>"
LABEL description="Billion-Dollar Autonomous AI Platform"
LABEL version="1.0.0"

# Environment variables
ENV WEBUI_NAME="InstaBids AI Hub"
ENV WEBUI_AUTH="True"
ENV ENABLE_WEBSOCKET_SUPPORT="True"
ENV GOOGLE_CLOUD_PROJECT="arched-logic-464602-d9"
ENV MCP_FACTORY_PORT="8888"
ENV PYTHONPATH="/app:/app/core"

# Install additional system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=python-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy MCP tools from builder
COPY --from=mcp-builder /build/mcp-server/dist /app/mcp-tools
COPY --from=mcp-builder /build/blueprints /app/blueprints

# Copy our core components
COPY core/mcp-factory/ /app/core/mcp-factory/
COPY core/autonomous-engine/ /app/core/autonomous-engine/
COPY openwebui-control/ /app/openwebui-control/

# Create supervisor configuration
RUN echo '[supervisord]\n\
nodaemon=true\n\
\n\
[program:openwebui]\n\
command=/app/backend/start.sh\n\
directory=/app/backend\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/openwebui.err.log\n\
stdout_logfile=/var/log/openwebui.out.log\n\
\n\
[program:mcp-factory]\n\
command=python /app/core/mcp-factory/server.py\n\
directory=/app/core/mcp-factory\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/mcp-factory.err.log\n\
stdout_logfile=/var/log/mcp-factory.out.log\n\
\n\
[program:autonomous-engine]\n\
command=python /app/core/autonomous-engine/main.py\n\
directory=/app/core/autonomous-engine\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/autonomous-engine.err.log\n\
stdout_logfile=/var/log/autonomous-engine.out.log' > /etc/supervisor/conf.d/supervisord.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 8888

# Start everything with supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
