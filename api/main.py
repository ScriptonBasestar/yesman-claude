from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"} 