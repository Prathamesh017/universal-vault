from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def hello():
    return {"message": "Hello World"}


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
