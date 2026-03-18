from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from utils.safeExecution import safeExecution
from typing import List
from Chroma.docling import (
    parse_doc,
    chunkDocs,
    encodeChunks,
    chunk_text_manual,
    encodeChunksManual,
)
from Chroma.db import (
    add_to_document_collection,
    query_document_collection,
    query_chat_collection,
    add_to_chat_collection,
)
from fastapi import UploadFile, File, Request
from datetime import datetime
import shutil
import os

router = APIRouter()


@router.get("/document/documents")
@safeExecution
async def getUserDocument(request: Request):
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state,"session_id",None)
    if user_id is None:
        return {"success": False, "message": "please login to get the document"}
    db = request.app.state.zensky_db
    docs_col = db["Documents"]
    # user_docs = docs_col.find({"user_id": user_id}).to_list(length=None) or []
    user_docs = list(docs_col.find())
    # print(user_docs)

    for doc in user_docs:
        doc["_id"] = str(doc["_id"])

    return {"success": True, "documents": user_docs}


@router.post("/document/upload_document")
@safeExecution
async def handle_upload_doc(request: Request, files: List[UploadFile] = File(...)):
    # print(request.state)
    user_id = getattr(request.state, "user_id", None)
    # print(user_id)
    if user_id is None:
        return {"success": False, "message": "Please login to upload a document"}

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    paths = []
    for file in files:
        paths.append(f"uploads/{file.filename}")
        with open(f"uploads/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    session_id = getattr(request.state, "session_id", None)
    # print(session_id)
    if session_id is None:
        return {"success": False, "message": "Can't upload document at the moment"}

    document_collection = request.app.state.document_collection
    if document_collection is None:
        return {"success": False, "message": "Can't upload document at the moment"}

    db = request.app.state.zensky_db
    if db is None:
        return {"success": False, "message": "Can't upload document at the moment"}
    docs_col = db["Documents"]
    if docs_col is None:
        return {"success": False, "message": "Can't upload document at the moment"}

    # parsed = parse_doc(path)
    # data = document_collection.get()
    # ids = data["ids"]
    # document_collection.delete(ids=ids)
    # docs_col.delete_many({})
    user_docs = []
    for path in paths:
        new_doc_info = {
            "name": path.split("/")[1],
            "uploadedOn": datetime.now(),
            "user_id": user_id,
        }
        new_doc = docs_col.insert_one(new_doc_info)
        user_docs.append({"id":str(new_doc.inserted_id)})
        # print("new doc ", new_doc)
        chunks = chunk_text_manual(path, 500)
        if chunks is not None:
            chunks = chunks[0]
            contents = [chunk["content"] for chunk in chunks]
            # print(path)
            # print(len(contents))
            embeddings = encodeChunksManual(contents)
            if len(embeddings) == 0:
                continue
            metadatas = [
                {
                    "session_id": session_id,
                    "document_id": str(new_doc.inserted_id),
                    "index": chunk["chunk_id"],
                    "topic": chunk["topic"],
                    "words": chunk["word_count"],
                    "page": chunk["page"],
                    "summary": chunk["summary"],
                    "user_id": user_id,
                    "pdf_name": path.split("/")[1],
                }
                for chunk in chunks
            ]
            add_to_document_collection(
                document_collection=document_collection,
                ids=[f"chunk={chunk['chunk_id']}" for chunk in chunks],
                embeddings=embeddings,
                chunks=contents,
                metadata=metadatas,
            )
        os.remove(path)



    return {"success": True,"documents":user_docs }
