from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.routers import sessions, controllers, config, logs, dashboard, websocket

app = FastAPI()

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

# Include web dashboard router
app.include_router(dashboard.router, tags=["web-dashboard"])

# Include WebSocket router
app.include_router(websocket.router, tags=["websocket"])

# Mount static files for web dashboard
app.mount("/static", StaticFiles(directory="web-dashboard/static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"} 