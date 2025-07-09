from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/hello")
def hello_world():
    return {"message": "Hello, World!"}

@app.get("/invalid")
def invalid_endpoint():
    return {"error": "Not Found"}, 404

@app.get("/nonexistent")
def nonexistent_endpoint():
    raise HTTPException(status_code=404, detail={"error": "Not Found"})