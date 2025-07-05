@echo off
REM Local development setup script for Fort Knox (Windows)

echo Setting up Fort Knox for local development...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed. Please install Docker Desktop first.
    echo Download from: https://www.docker.com/products/docker-desktop/
    exit /b 1
)

REM Check if docker-compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo docker-compose is not installed. It should come with Docker Desktop.
    exit /b 1
)

echo Docker and docker-compose are installed

REM Create necessary directories
echo Creating necessary directories...
if not exist "credentials" mkdir credentials
if not exist "shared-memory" mkdir shared-memory
if not exist "mcp-tools\generated" mkdir mcp-tools\generated

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    if exist ".env.example" (
        copy .env.example .env
    ) else (
        echo No .env.example found, using defaults
    )
)

REM Install MCP server dependencies
echo Installing MCP server dependencies...
cd mcp-server
call npm install
call npm run build
cd ..

REM Build Docker images
echo Building Docker images...
docker-compose build

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Add your Google Cloud service account key to: credentials\service-account-key.json
echo 2. Update the .env file with your configuration
echo 3. Run: docker-compose up
echo 4. Access Open WebUI at: http://localhost:8080
echo 5. MCP Server will be available at: http://localhost:8888
echo.
echo To start the system: docker-compose up
echo To stop the system: docker-compose down
echo To view logs: docker-compose logs -f
