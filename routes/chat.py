from fastapi import APIRouter, Request
from constants import creativity_levels
from utils.safeExecution import safeExecution
import torch
import pymupdf
import time
from utils.orderDocs import orderDocument, orderChats
from fastapi.responses import StreamingResponse, Response

# from server import llm_model,llm
from Model.model import (
    format_user_query,
    format_messages,
    generate_response,
    text_to_tokens,
    tokens_to_text,
    text_to_tokens,
)

from fastapi import UploadFile, File, Request, APIRouter
import shutil
import os
from datetime import datetime
from utils.queryProcessing import queryPreprocessing

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

router = APIRouter()


@router.post("/chat/query")
@safeExecution
async def handle_chat_response(request: Request):
    user_id = request.state.user_id
    body = await request.json()

    db = request.app.state.zensky_db
    chat_col = db["Chats"]

    # model = request.app.state.model
    # tokenizer = request.app.state.tokenizer

    query = body["query"]
    chat_id = body["chat_id"] if "chat_id" in body else None
    document_ids = body["document_ids"] if "document_ids" in body else None
    query = queryPreprocessing(query)

    creativity = body["creativity"] or "medium"
    session_id = request.state.session_id
    embeddings = encodeChunksManual([query])

    document_collection = request.app.state.document_collection
    relevant_docs = query_document_collection(
        document_collection=document_collection,
        query_embedding=embeddings,
        top_k=5,
        condition={"document_id": {"$in": document_ids}},
    )

    ordered_documents = orderDocument(
        relevant_docs["metadatas"][0],
        relevant_docs["documents"][0],
    )

    chat_collection = request.app.state.chat_collection
    condition = {}

    condition["chat_id"] = chat_id or ""

    if session_id:
        condition["session_id"] = session_id

    if user_id:
        condition["user_id"] = user_id

    relevant_chats = query_chat_collection(
        chat_collection=chat_collection,
        query_embedding=embeddings,
        top_k=5,
        condition=condition,
    )

    ids = relevant_chats["ids"]

    ordered_chats = (
        orderChats(
            relevant_chats["metadatas"][0],
            relevant_chats["documents"][0],
        )
        if len(ids) > 0
        else []
    )
    chat_document = None
    if chat_id is not None:
        chat_document = chat_col.find({"chat_id": chat_id})

    message = format_user_query(query, ordered_documents, ordered_chats)

    # inputs = format_messages(message, tokenizer)

    # streamer = generate_response(
    #     inputs,
    #     model,
    #     tokenizer,
    #     200,
    #     creativity_levels[creativity],
    # )
    client = request.app.state.client
    if client is None:
        return {"success": False, "message": "Failed to respond to query."}
    stream = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Can u please write me a short code of python loop to teach how it works",
            }
        ],
        stream=True,
    )
    response = ""
    endTime = None
    for token in stream:
        if endTime is None:
            endTime = time.time()
        content = token.choices[0].delta.content
        if content:
            response += content
        # print(content)
    print(response)

    # Streaming generator
    async def token_generator():

        response_tokens = []
        endTime = None

        for token in stream:
            if endTime is None:
                endTime = time.time()
            content = token.choices[0].delta.content
            # print(content)
            response_tokens.append(content)
            # yield content  # send token to client immediately
        print(response_tokens)
        timestamp = datetime.now()
        # AFTER STREAM FINISHES
        final_response = "".join(response_tokens)

        # if chat_document is None:
        #     result = chat_col.insert_one(
        #         {
        #             "createdAt": timestamp,
        #             "chat_id": chat_id,
        #             "messages": [{"user": query, "assistant": final_response}],
        #             "user_id": user_id,
        #             "session_id": session_id,
        #         }
        #     )

        ## chat_id = str(result.inserted_id)

        # else:
        #     chat_col.update_one(
        #         {"_id": chat_document["_id"]},
        #         {"$push": {"messages": {"user": query, "assistant": final_response}}},
        #     )
        # chat_embeddings = encodeChunksManual([final_response])
        # add_to_chat_collection(
        #     ids=[str(timestamp)],
        #     chat_collection=chat_collection,
        #     embeddings=chat_embeddings,
        #     chunks=[final_response],
        #     metadata={
        #         "session_id": session_id,
        #         "timestamp": str(timestamp),
        #         "user_id": user_id,
        #         "chat_id": chat_id,
        #     },
        # )

    # return StreamingResponse(token_generator(), media_type="text/plain")
    return {"success": True, "chat_id": chat_id}


@router.get("/chat/getChats")
@safeExecution
async def getUserChats(request: Request, response: Response):
    user_id = request.state.user_id
    body = request.json()
    chat_id = body["chat_id"] or None
    if user_id is None:
        return {"success": False, "chats": None}
    if chat_id is None:
        return {"success": True, "chats": []}
    db = request.app.state.zensky_db
    chat_col = db["Chats"]
    user_chats = chat_col.find({"user_id": user_id,"chat_id":chat_id})
    return {"success": True, "chats": user_chats}
