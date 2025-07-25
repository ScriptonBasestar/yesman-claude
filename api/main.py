import asyncio
import os
from datetime import UTC, datetime
from typing import TypedDict, cast

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Scope

from api.background_tasks import task_runner
from api.middleware.error_handler import add_request_id_middleware, global_error_handler
from api.routers import config, controllers, dashboard, logs, sessions, websocket_router
from api.routers.websocket_router import ConnectionManager
from libs.core.error_handling import YesmanError

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


# Type definitions for API responses
class TaskStateDict(TypedDict):
    """Type definition for individual task state."""

    is_running: bool
    last_run: str | None
    error_count: int
    interval: int | float | None


class TaskStatesDict(TypedDict):
    """Type definition for task runner states response."""

    is_running: bool
    tasks: dict[str, TaskStateDict]


class ConnectionStatsDict(TypedDict):
    """Type definition for WebSocket connection statistics."""

    total_connections: int
    channels: dict[str, int]


class BatchStatisticsDict(TypedDict):
    """Type definition for batch processor statistics."""

    batches_processed: int
    entries_processed: int
    bytes_written: int
    compression_ratio: float
    avg_batch_size: float
    files_created: int
    pending_entries: int
    current_file_size: int
    max_batch_size: int
    max_batch_time: float
    compression_enabled: bool
    uptime_seconds: float


class WebSocketStatsDict(TypedDict):
    """Type definition for WebSocket stats endpoint response."""

    connection_stats: ConnectionStatsDict
    batch_stats: BatchStatisticsDict
    summary: str


app = FastAPI(title="Yesman Claude API", version="0.1.0")

# Create WebSocket connection manager
manager = ConnectionManager()

# Add error handling middleware
app.add_exception_handler(YesmanError, global_error_handler)
app.add_exception_handler(StarletteHTTPException, global_error_handler)
app.add_exception_handler(RequestValidationError, global_error_handler)
app.add_exception_handler(Exception, global_error_handler)

# Add request ID middleware
app.middleware("http")(add_request_id_middleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(controllers.router, prefix="/api", tags=["controllers"])
app.include_router(config.router, prefix="/api", tags=["configuration"])
app.include_router(logs.router, prefix="/api", tags=["logs"])

# Include dashboard API router (for SvelteKit)
app.include_router(dashboard.router, tags=["dashboard-api"])

# Include WebSocket router
app.include_router(websocket_router.router, tags=["websocket"])

# Mount SvelteKit assets
sveltekit_build_path = "tauri-dashboard/build"
if os.path.exists(sveltekit_build_path):
    # Mount SvelteKit static files
    fonts_path = "tauri-dashboard/build/fonts"
    if os.path.exists(fonts_path):
        app.mount("/fonts", StaticFiles(directory=fonts_path), name="fonts")
    # Mount SvelteKit static assets with cache control headers

    class CacheControlStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope: Scope) -> Response:
            response = await super().get_response(path, scope)
            if hasattr(response, "headers"):
                # Add cache-busting headers for JavaScript files
                if path.endswith(".js"):
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                # Cache assets with hash in filename for longer
                elif any(path.endswith(ext) for ext in [".css", ".png", ".jpg", ".svg", ".woff", ".woff2"]):
                    response.headers["Cache-Control"] = "public, max-age=31536000"
            return response

    app.mount(
        "/_app",
        CacheControlStaticFiles(directory="tauri-dashboard/build/_app"),
        name="app-assets",
    )


# Health check endpoint
@app.get("/healthz")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and load balancer."""
    return {
        "status": "healthy",
        "service": "yesman-claude-api",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "0.1.0",
    }


# API info endpoint
@app.get("/api")
async def api_info() -> dict[str, str | dict[str, str] | None]:
    """API information and available endpoints."""
    return {
        "service": "Yesman Claude API",
        "version": "0.1.0",
        "endpoints": {
            "sessions": "/api/sessions",
            "controllers": "/api/controllers",
            "config": "/api/config",
            "logs": "/api/logs",
            "dashboard": "/api/dashboard",
            "websocket": "/ws",
            "health": "/healthz",
        },
        "ui": {
            "dashboard": "/" if os.path.exists(sveltekit_build_path) else None,
        },
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# SvelteKit dashboard route (serves at root)
if os.path.exists(sveltekit_build_path):

    @app.get("/")
    @app.get("/{path:path}")
    async def serve_dashboard(path: str = "") -> FileResponse:
        """Serve SvelteKit dashboard at root."""
        # Skip API routes and specific endpoints
        if path.startswith(("api/", "docs", "openapi.json", "healthz", "_app/", "fonts/")):
            raise HTTPException(status_code=404, detail="Not found")

        # For SPA, always serve index.html with cache-busting headers
        response = FileResponse("tauri-dashboard/build/index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

else:
    # Development mode: provide a basic dashboard page when Tauri build is not available
    @app.get("/")
    async def serve_dev_dashboard() -> Response:
        """Serve development dashboard when SvelteKit build is not
        available."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Yesman Dashboard - Development Mode</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
                .status { background: #e8f5e8; border: 1px solid #4CAF50; padding: 15px; border-radius: 4px; margin: 20px 0; }
                .api-links { background: #f8f9fa; padding: 20px; border-radius: 4px; margin: 20px 0; }
                .api-links a { display: block; margin: 5px 0; color: #007bff; text-decoration: none; }
                .api-links a:hover { text-decoration: underline; }
                .note { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Yesman Dashboard - Development Mode</h1>

                <div class="status">
                    <strong>✅ API Server Status:</strong> Running successfully on this port<br>
                    <strong>🕐 Started:</strong> {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}
                </div>

                <div class="note">
                    <strong>📝 Development Mode Active</strong><br>
                    The full SvelteKit dashboard is not built. This is a basic development interface.
                </div>

                <div class="api-links">
                    <h3>🔗 Available API Endpoints:</h3>
                    <a href="/docs" target="_blank">📚 API Documentation (FastAPI Docs)</a>
                    <a href="/api" target="_blank">🔍 API Info</a>
                    <a href="/healthz" target="_blank">❤️ Health Check</a>
                    <a href="/api/tasks/status" target="_blank">📊 Task Status</a>
                    <a href="/api/websocket/stats" target="_blank">🌐 WebSocket Stats</a>
                </div>

                <div class="api-links">
                    <h3>🛠️ Development Instructions:</h3>
                    <p>To access the full dashboard interface:</p>
                    <ol>
                        <li>Build the Tauri dashboard: <code>cd tauri-dashboard && npm run build</code></li>
                        <li>Or use the TUI interface: <code>yesman.py dashboard run -i tui</code></li>
                        <li>Or access Vite dev server at: <a href="http://localhost:5173" target="_blank">http://localhost:5173</a></li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Start background tasks on application startup."""
    asyncio.create_task(task_runner.start())


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background tasks on application shutdown."""
    await task_runner.stop()

    # Shutdown WebSocket manager and batch processor
    await manager.shutdown()


# Add endpoint to check task status
@app.get("/api/tasks/status")
async def get_task_status() -> TaskStatesDict:
    """Get status of background tasks."""
    return {
        "is_running": task_runner.is_running,
        "tasks": cast(dict[str, TaskStateDict], task_runner.get_task_states()),
    }


# Add endpoint to check WebSocket batch processing stats
@app.get("/api/websocket/stats")
async def get_websocket_stats() -> WebSocketStatsDict:
    """Get WebSocket connection and batch processing statistics."""
    connection_stats = manager.get_connection_stats()
    batch_stats = manager.get_batch_statistics()

    return {
        "connection_stats": cast(ConnectionStatsDict, connection_stats),
        "batch_stats": cast(BatchStatisticsDict, batch_stats),
        "summary": datetime.now(UTC).isoformat(),
    }
