from fastapi import APIRouter, Request
from constants import creativity_levels
from utils.safeExecution import safeExecution
import time
import uuid
from utils.orderDocs import orderDocument, orderChats,sort_docs,sort_chats
from fastapi.responses import StreamingResponse, Response
from startupFunctions import get_model_client,get_mongo,get_qdrant

# from server import llm_model,llm
# from Model.model import (
#     format_user_query,
#     format_messages,
#     text_to_tokens,
#     tokens_to_text,
#     text_to_tokens,
# )

from fastapi import UploadFile, File, Request, APIRouter
import shutil
import os
from datetime import datetime
from utils.queryProcessing import queryPreprocessing

from Qdrant.docling import (
    chunk_text_manual,
    encodeChunksManual,
)
from Qdrant.db import add_to_collection, query_qdrant_db

router = APIRouter()



import logging

logger = logging.getLogger("chat_routes")
logging.basicConfig(level=logging.INFO)

@router.get("/chat/newChat")
@safeExecution
def create_new_chat(request: Request):
    new_chat_id = uuid.uuid4()
    sessions = request.app.state.sessions
    session_id = getattr(request.state, "session_id", None)

    logger.info(f"Creating new chat | session_id={session_id} | chat_id={new_chat_id}")

    if session_id:
        sessions[session_id]["current_chat_id"] = new_chat_id
    else:
        logger.warning("Session ID missing while creating chat")

    return {"success": True, "chatId": new_chat_id}

@router.get("/chat/getChats")
@safeExecution
async def getUserChats(request: Request, response: Response):
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)

    logger.info(f"Fetching chats | user_id={user_id} | session_id={session_id}")

    if session_id is None:
        logger.warning("No session_id, returning empty chats")
        return {"success": True, "chats": []}

    condition = {}
    if user_id is None:
        condition["session_id"] = session_id
    else:
        condition["user_id"] = user_id

    db = get_mongo(request.app)
    if db is None:
        logger.error("MongoDB not available")
        return {"success": False, "message": "DB error"}

    chat_col = db["Chats"]
    user_chats_cursor = chat_col.find(condition).sort("createdAt", -1)
    user_chats = [serialize_chat(chat) for chat in user_chats_cursor]

    logger.info(f"Fetched {len(user_chats)} chats")

    return {"success": True, "chats": user_chats}


def serialize_chat(chat):
    chat["_id"] = str(chat["_id"])
    return chat


@router.get("/chat/getChatId")
@safeExecution
def getChatId(request: Request):
    current_chat_id = request.state.session.get("current_chat_id")
    return {"success": True, "chatId": current_chat_id}


@router.post("/chat/setChatId")
@safeExecution
async def setChatId(request: Request):
    sessions = request.app.state.sessions
    body = await request.json()

    clientChatId = body["chatId"]
    session_id = getattr(request.state, "session_id", None)

    logger.info(f"Setting chat_id | session_id={session_id} | chat_id={clientChatId}")

    if session_id and clientChatId:
        sessions[session_id]["current_chat_id"] = clientChatId
    else:
        logger.warning("Failed to set chat_id (missing session or chatId)")

    return {"success": True}

@router.post("/chat/query")
@safeExecution
async def handle_chat_response(request: Request):
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)

    body = await request.json()

    query = body["query"]
    selected_chat_id = body["selected_chat_id"]
    chat_id = request.state.session.get("current_chat_id")

    chat_id_using = selected_chat_id or chat_id

    logger.info(f"Incoming query | session_id={session_id} | user_id={user_id}")
    logger.info(f"Chat selection | selected={selected_chat_id} | session_chat={chat_id} | using={chat_id_using}")

    document_ids = body.get("document_ids", [])
    query = queryPreprocessing(query)

    db = get_mongo(request.app)
    chat_col = db["Chats"]

    embeddings = encodeChunksManual([query])
    if not embeddings:
        logger.error("Failed to generate query embeddings")
        return {"success": False, "message": "Embedding failed"}

    qdrant_client = get_qdrant(request.app)

    logger.info(f"Querying Qdrant documents | doc_ids={document_ids}")

    relevant_docs = query_qdrant_db(
        qdrant_client=qdrant_client,
        collection_name="document_collection",
        query_vector=embeddings[0],
        top_k=3,
        condition={"document_id": {"$in": document_ids}},
    )

    ordered_documents = sort_docs(relevant_docs)

    condition = {"chat_id": chat_id_using or ""}

    if session_id:
        condition["session_id"] = session_id
    if user_id:
        condition["user_id"] = user_id

    logger.info(f"Querying Qdrant chats | condition={condition}")

    relevant_chats = query_qdrant_db(
        qdrant_client=qdrant_client,
        collection_name="chat_collection",
        query_vector=embeddings[0],
        top_k=3,
        condition=condition,
    )

    ordered_chats = sort_chats(relevant_chats)

    chat_document = None
    if chat_id_using:
        chat_document = chat_col.find_one({"chat_id": chat_id_using})

    logger.info(f"Chat document exists: {chat_document is not None}")

    client = get_model_client(request.app)
    if client is None:
        logger.error("Model client not available")
        return {"success": False, "message": "LLM error"}

    content = "\n\n".join(ordered_documents + ordered_chats)

    messages = [
        {"role": "system", "content": f"<context>{content}</context>"},
        {"role": "user", "content": query},
    ]

    stream = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        stream=True,
    )

    async def token_generator():
        response_tokens = ""

        try:
            for token in stream:
                delta = token.choices[0].delta
                content = getattr(delta, "content", None)

                if content:
                    response_tokens += content
                    yield content

            final_response = query + response_tokens
            timestamp = datetime.now()

            logger.info(f"Saving chat response | chat_id={chat_id_using}")

            if chat_document is None:
                logger.info("Creating new chat document")

                chat_col.insert_one(
                    {
                        "chat_id": chat_id_using,
                        "messages": [
                            {"role": "user", "content": query},
                            {"role": "assistant", "content": final_response},
                        ],
                        "user_id": user_id or "no_user_id",
                        "session_id": session_id,
                        "name": query,
                        "createdAt": datetime.utcnow(),
                    }
                )
            else:
                logger.info("Updating existing chat document")

                chat_col.update_one(
                    {"chat_id": chat_id_using},
                    {
                        "$push": {
                            "messages": {
                                "$each": [
                                    {"role": "user", "content": query},
                                    {"role": "assistant", "content": final_response},
                                ]
                            }
                        }
                    },
                )

            chat_embeddings = encodeChunksManual([final_response])

            logger.info("Saving chat embeddings to Qdrant")

            add_to_collection(
                ids=[str(timestamp)],
                qdrant_client=qdrant_client,
                collection_name="chat_collection",
                embeddings=chat_embeddings,
                metadata=[{
                    "session_id": session_id,
                    "user_id": user_id or "no_user_id",
                    "chat_id": chat_id_using,
                    "text": final_response,
                }],
            )

        except Exception as e:
            logger.exception(f"Streaming error: {str(e)}")
            yield "Error generating response"

    return StreamingResponse(token_generator(), media_type="text/plain")