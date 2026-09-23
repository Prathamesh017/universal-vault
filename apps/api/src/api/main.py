from fastapi import FastAPI, File, UploadFile

from api.parser import parse_document
from api.chunking import create_chunks_from_structure

app = FastAPI()


@app.get("/")
def hello():
    return {"message": "Hello World"}


@app.post("/parse")
async def parse(file: UploadFile = File(...)):
    contents = await file.read()
    text = contents.decode("utf-8")
    structure = parse_document(text)

    return {
        "filename": file.filename,
        "title": structure.get("title"),
        "chunks": create_chunks_from_structure(structure),
        "structure": structure,
    }

def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
