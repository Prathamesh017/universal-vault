from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.db.database import init_db
from api.router.chunks import router as chunks_router
from api.router.documents import router as documents_router
from api.router.embed import router as embed_router
from api.router.upload import router as upload_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(upload_router)
app.include_router(documents_router)
app.include_router(embed_router)
app.include_router(chunks_router)


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
