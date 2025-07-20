import asyncio
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.background_tasks import task_runner
from api.middleware.error_handler import add_request_id_middleware, global_error_handler
from api.routers import config, controllers, dashboard, logs, sessions, websocket_router
from libs.core.error_handling import YesmanError

app = FastAPI(title="Yesman Claude API", version="0.1.0")

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

# Mount SvelteKit static files
app.mount("/fonts", StaticFiles(directory="tauri-dashboard/build/fonts"), name="fonts")

# Mount SvelteKit assets
sveltekit_build_path = "tauri-dashboard/build"
if os.path.exists(sveltekit_build_path):
    # Mount SvelteKit static assets with cache control headers
    from fastapi.staticfiles import StaticFiles

    class CacheControlStaticFiles(StaticFiles):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

        async def get_response(self, path: str, scope: Any):
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
async def health_check():
    """Health check endpoint for monitoring and load balancer."""
    return {
        "status": "healthy",
        "service": "yesman-claude-api",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
    }


# API info endpoint
@app.get("/api")
async def api_info():
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
    from fastapi.responses import FileResponse

    @app.get("/")
    @app.get("/{path:path}")
    async def serve_dashboard(path: str = ""):
        """Serve SvelteKit dashboard at root."""
        # Skip API routes and specific endpoints
        if path.startswith(("api/", "docs", "openapi.json", "healthz", "_app/", "fonts/")):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not found")

        # For SPA, always serve index.html with cache-busting headers
        response = FileResponse("tauri-dashboard/build/index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


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
    from api.routers.websocket_router import manager

    await manager.shutdown()


# Add endpoint to check task status
@app.get("/api/tasks/status")
async def get_task_status():
    """Get status of background tasks."""
    return {
        "is_running": task_runner.is_running,
        "tasks": task_runner.get_task_states(),
    }


# Add endpoint to check WebSocket batch processing stats
@app.get("/api/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection and batch processing statistics."""
    from api.routers.websocket_router import manager

    connection_stats = manager.get_connection_stats()
    batch_stats = manager.get_batch_statistics()

    return {
        "connections": connection_stats,
        "batch_processing": batch_stats,
        "timestamp": datetime.now().isoformat(),
    }
