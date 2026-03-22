from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from utils.safeExecution import safeExecution
from typing import List
from Qdrant.docling import (
    chunk_text_manual,
    encodeChunksManual,
)
from startupFunctions import get_mongo,get_qdrant,get_model_client
from Qdrant.db import add_to_collection
from fastapi import UploadFile, File, Request
from datetime import datetime
import shutil
import os

router = APIRouter()


@router.get("/document/documents")
@safeExecution
async def getUserDocument(request: Request):
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)
    if user_id and session_id is None:
        return {"success": False, "message": "please login to get the document"}
    condition = {}
    if user_id is None:
        condition["session_id"] = session_id
    else:
        condition["user_id"] = user_id
    db = get_mongo(request.app)
    docs_col = db["Documents"]
    user_docs_cursor = docs_col.find(condition).sort("createdAt", -1)
    user_docs = [serializeDoc(doc) for doc in user_docs_cursor]
    return {"success": True, "documents": user_docs}


def serializeDoc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.post("/document/upload_document")
@safeExecution
async def handle_upload_doc(request: Request, files: List[UploadFile] = File(...)):
    user_id = getattr(request.state, "user_id", None)

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    paths = []
    for file in files:
        paths.append(f"uploads/{file.filename}")
        with open(f"uploads/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    session_id = getattr(request.state, "session_id", None)
    if session_id is None:
        return {"success": False, "message": "Can't upload document at the moment"}

    qdrant_client = get_qdrant(request.app)
    if qdrant_client is None:
        return {"success": False, "message": "Can't upload document at the moment"}
    model_client = get_model_client(request.app)
    db = get_mongo(request.app)
    if db is None:
        return {"success": False, "message": "Can't upload document at the moment"}
    docs_col = db["Documents"]
    if docs_col is None:
        return {"success": False, "message": "Can't upload document at the moment"}

    user_docs = []
    for path in paths:
        new_doc_info = {
            "name": path.split("/")[1],
            "uploadedOn": datetime.now(),
            "user_id": user_id or "no_user_id",
            "session_id": session_id,
            "createdAt": datetime.utcnow(),
        }
        new_doc = docs_col.insert_one(new_doc_info)
        user_docs.append({"_id": str(new_doc.inserted_id)})
        chunks = chunk_text_manual(path, 500)
        if chunks is not None:
            chunks = chunks[0]
            contents = [chunk["content"] for chunk in chunks]
            embeddings = encodeChunksManual(contents)
            if len(embeddings) == 0:
                continue
            metadatas = [
                {
                    "tenant_id": user_id or "no_user_id",  
                    "session_id": session_id,
                    "document_id": str(new_doc.inserted_id),
                    "chunk_index": chunk["chunk_id"],
                    "topic": chunk["topic"],
                    "words": chunk["word_count"],
                    "page": chunk["page"],
                    "summary": chunk["summary"],
                    "pdf_name": path.split("/")[1],
                    "text": chunk["content"],  
                }
                for chunk in chunks
            ]
            add_to_collection(
                qdrant_client=qdrant_client,
                ids=[f"chunk={chunk['chunk_id']}" for chunk in chunks],
                collection_name="document_collection",
                embeddings=embeddings,
                metadata=metadatas,
            )
        os.remove(path)

    return {"success": True, "documents": user_docs}
