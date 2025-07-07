from fastapi import FastAPI
from api.routers import sessions, controllers

app = FastAPI()

app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(controllers.router, prefix="/api", tags=["controllers"])

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"} 