@echo off
echo ============================================
echo Fort Knox Local Development Quick Start
echo ============================================
echo.

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [OK] Docker is installed

REM Create directories
echo Creating necessary directories...
if not exist "credentials" mkdir credentials
if not exist "shared-memory" mkdir shared-memory
if not exist "mcp-tools\generated" mkdir mcp-tools\generated

REM Create a minimal docker-compose for development
echo Creating development docker-compose...
(
echo version: '3.8'
echo.
echo services:
echo   # For now, let's just run Open WebUI and Redis
echo   openwebui:
echo     image: ghcr.io/open-webui/open-webui:main
echo     ports:
echo       - "8080:8080"
echo     volumes:
echo       - openwebui_data:/app/backend/data
echo       - ./agents:/app/agents
echo       - ./fort-knox-apis:/app/fort-knox-apis
echo     environment:
echo       - DATA_DIR=/app/backend/data
echo       - WEBUI_SECRET_KEY=your-secret-key-here
echo       - ENABLE_SIGNUP=false
echo     networks:
echo       - fort-knox-network
echo.
echo   redis:
echo     image: redis:7-alpine
echo     ports:
echo       - "6379:6379"
echo     volumes:
echo       - redis_data:/data
echo     networks:
echo       - fort-knox-network
echo.
echo volumes:
echo   openwebui_data:
echo   redis_data:
echo.
echo networks:
echo   fort-knox-network:
echo     driver: bridge
) > docker-compose-dev.yml

echo.
echo ============================================
echo Setup Complete! 
echo ============================================
echo.
echo To start the development environment:
echo   docker-compose -f docker-compose-dev.yml up -d
echo.
echo This will start:
echo   - Open WebUI at http://localhost:8080
echo   - Redis at localhost:6379
echo.
echo To stop:
echo   docker-compose -f docker-compose-dev.yml down
echo.
echo To view logs:
echo   docker-compose -f docker-compose-dev.yml logs -f
echo.
pause
