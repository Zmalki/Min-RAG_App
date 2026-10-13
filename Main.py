from fastapi import FastAPI
app = FastAPI()

@app.get("/welcome")
def welcome():
    return {"message": "Welcome to Min_RAG_App!"
    }