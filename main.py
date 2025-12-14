from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
import uvicorn
from config.settings import settings
from mcp_tools import get_mcp_tools_info
from services import github_service, docker_service, filesystem_service
from langchain_integration import service as langchain_service

# Initialize FastAPI application
app = FastAPI(
    title="MCP Developer Assistant",
    description="AI-powered developer tools via Model Context Protocol (MCP). Provides GitHub, Docker, and filesystem operations for AI agents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "MCP Developer Assistant",
            "version": "1.0.0",
            "docs": "/docs"
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "github_configured": bool(settings.github_token),
            "openai_configured": bool(settings.openai_api_key)
        }
    )


@app.get("/mcp/tools", tags=["MCP"])
async def list_mcp_tools():
    """List all available MCP tools by category."""
    return JSONResponse(
        content={
            "tools": get_mcp_tools_info(),
            "total_categories": 3
        }
    )


# Include service routers
app.include_router(github_service.router, prefix="/github", tags=["GitHub"])
app.include_router(docker_service.router, prefix="/docker", tags=["Docker"])
app.include_router(filesystem_service.router, prefix="/filesystem", tags=["Filesystem"])
app.include_router(langchain_service.router, prefix="/ai", tags=["AI Agent"])

# Initialize MCP Server (must be after all routes are defined)
mcp_server = FastApiMCP(
    fastapi=app,
    name="dev-assistant",
    description="Developer Assistant MCP Server - Provides GitHub, Docker, and filesystem operations"
)


# Application startup
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

