from fastapi import FastAPI
from api.router.upload import router as upload_router


app = FastAPI()
app.include_router(upload_router)


def main() -> None:
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
