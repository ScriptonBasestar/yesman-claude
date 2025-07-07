from fastapi import FastAPI
from api.routers import sessions

app = FastAPI()

app.include_router(sessions.router, prefix="/api", tags=["sessions"])

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"} 