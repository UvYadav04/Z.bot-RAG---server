from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from utils.safeExecution import safeExecution
from typing import List
from Qdrant.docling import chunk_text_manual, encodeChunksManual
from startupFunctions import get_mongo, get_qdrant, get_model_client
from Qdrant.db import add_to_collection
from datetime import datetime
import shutil
import os
import logging

router = APIRouter()

# Configure logger
logger = logging.getLogger("document_routes")
logging.basicConfig(level=logging.INFO)


@router.get("/document/documents")
@safeExecution
async def getUserDocument(request: Request):
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)

    logger.info(f"Fetching documents | user_id={user_id} | session_id={session_id}")

    if user_id and session_id is None:
        logger.warning("User has user_id but missing session_id")
        return {"success": False, "message": "please login to get the document"}

    condition = {}
    if user_id is None:
        condition["session_id"] = session_id
    else:
        condition["user_id"] = user_id

    db = get_mongo(request.app)
    if db is None:
        logger.error("MongoDB connection not available")
        return {"success": False, "message": "DB connection failed"}

    docs_col = db["Documents"]
    user_docs_cursor = docs_col.find(condition).sort("createdAt", -1)

    user_docs = [serializeDoc(doc) for doc in user_docs_cursor]

    logger.info(f"Fetched {len(user_docs)} documents")

    return {"success": True, "documents": user_docs}


def serializeDoc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.post("/document/upload_document")
@safeExecution
async def handle_upload_doc(request: Request, files: List[UploadFile] = File(...)):
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)

    logger.info(f"Upload request | user_id={user_id} | session_id={session_id} | files={len(files)}")

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    paths = []
    for file in files:
        file_path = f"uploads/{file.filename}"
        paths.append(file_path)

        logger.info(f"Saving file: {file.filename}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    if session_id is None:
        logger.warning("Missing session_id during upload")
        return {"success": False, "message": "Can't upload document at the moment"}

    qdrant_client = get_qdrant(request.app)
    if qdrant_client is None:
        logger.error("Qdrant client not available")
        return {"success": False, "message": "Can't upload document at the moment"}

    model_client = get_model_client(request.app)
    if model_client is None:
        logger.warning("Model client is None (embeddings may fail)")

    db = get_mongo(request.app)
    if db is None:
        logger.error("MongoDB not available")
        return {"success": False, "message": "Can't upload document at the moment"}

    docs_col = db["Documents"]
    if docs_col is None:
        logger.error("Documents collection not found")
        return {"success": False, "message": "Can't upload document at the moment"}

    user_docs = []

    for path in paths:
        try:
            logger.info(f"Processing file: {path}")

            new_doc_info = {
                "name": path.split("/")[1],
                "uploadedOn": datetime.now(),
                "user_id": user_id or "no_user_id",
                "session_id": session_id,
                "createdAt": datetime.utcnow(),
            }

            new_doc = docs_col.insert_one(new_doc_info)
            doc_id = str(new_doc.inserted_id)

            logger.info(f"Inserted document in MongoDB | doc_id={doc_id}")

            user_docs.append({"_id": doc_id})

            chunks = chunk_text_manual(path, 200)

            if chunks is None:
                logger.warning(f"No chunks generated for {path}")
                continue

            chunks = chunks[0]
            contents = [chunk["content"] for chunk in chunks]

            logger.info(f"Generated {len(contents)} chunks")

            embeddings = encodeChunksManual(contents)

            if len(embeddings) == 0:
                logger.warning(f"No embeddings generated for {path}")
                continue

            metadatas = [
                {
                    "tenant_id": user_id or "no_user_id",
                    "session_id": session_id,
                    "document_id": doc_id,
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

            logger.info(f"Uploading {len(embeddings)} embeddings to Qdrant")

            add_to_collection(
                qdrant_client=qdrant_client,
                ids=[f"chunk={chunk['chunk_id']}" for chunk in chunks],
                collection_name="document_collection",
                embeddings=embeddings,
                metadata=metadatas,
            )

            logger.info(f"Successfully stored embeddings for doc_id={doc_id}")

        except Exception as e:
            logger.exception(f"Error processing file {path}: {str(e)}")

        finally:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Deleted temp file: {path}")

    return {"success": True, "documents": user_docs}s