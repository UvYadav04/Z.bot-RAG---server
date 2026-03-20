import chromadb
from utils.safeExecution import safeExecution
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
)
from dotenv import load_dotenv

load_dotenv()
import os

from qdrant_client.models import VectorParams, Distance


@safeExecution
def instantiate_chroma():
    my_qdrant_client = QdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY"),
    )
    # my_qdrant_client.recreate_collection(
    #     collection_name="document_collection",
    #     vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    # )
    # my_qdrant_client.recreate_collection(
    #     collection_name="chat_collection",
    #     vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    # )
    return my_qdrant_client


import traceback


# @safeExecution
def add_to_collection(ids, qdrant_client, collection_name, embeddings, metadata):
    try:
        points = [
            {
                "id": i,
                "vector": embeddings[i],
                "payload": metadata[i],
            }
            for i in range(len(ids))
        ]

        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
        )

    except Exception as e:
        print(e)
        traceback.print_exc()


@safeExecution
def query_qdrant_db(
    qdrant_client, collection_name, query_vector, top_k=5, condition=None
):

    qdrant_filter = build_filter(condition=condition)

    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        query_filter=qdrant_filter,
    )

    formatted_results = [
        {
            "id": point.id,
            "score": point.score,
            "text": point.payload.get("text"),
            "metadata": point.payload,
        }
        for point in results
    ]
    print(formatted_results)

    return formatted_results


def build_filter(condition):
    if not condition:
        return None

    must_conditions = []

    for key, value in condition.items():

        # 🔥 Handle $in
        if isinstance(value, dict) and "$in" in value:
            must_conditions.append(
                FieldCondition(key=key, match=MatchAny(any=value["$in"]))
            )

        # ✅ Normal equality
        else:
            must_conditions.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )

    return Filter(must=must_conditions)


"""
document_collection_schema = {
embeddings=[],
chunks:[],
metadata:{
    userId:abc,
    sessionId:adfb2334b,
    document_name: resume.pdf,
    content_type:'pdf'
    }
}

chat_collection_schema = {
embeddings=[],
chunks:[],
metadata:{
    userId:abc,
    sessionId:adfb2334b,
    date:12/03/2025,
    time: 12.34,
    chatId:234kd32f
    }
}
"""
