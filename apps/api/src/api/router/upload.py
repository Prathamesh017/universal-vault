from fastapi import APIRouter, File, Form, UploadFile

from api.service.handle_upload import process_upload

router = APIRouter()


@router.get("/")
def hello():
    return {"message": "Hello World"}


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    description: str = Form(default=""),
):
    contents = await file.read()
    text = contents.decode("utf-8")
    result = process_upload(
        file.filename or "untitled.md",
        text,
        description=description,
    )

    return {
        "document": result["document"],
        "chunks": result["chunks"],
        "structure": result["structure"],
    }
