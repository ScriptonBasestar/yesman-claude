from fastapi import FastAPI
from api.routers import sessions, controllers, config, logs

app = FastAPI()

app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(controllers.router, prefix="/api", tags=["controllers"])
app.include_router(config.router, prefix="/api", tags=["configuration"])
app.include_router(logs.router, prefix="/api", tags=["logs"])

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"} 