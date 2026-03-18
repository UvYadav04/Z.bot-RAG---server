import chromadb
from utils.safeExecution import safeExecution


@safeExecution
def instantiate_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    document_collection = client.get_or_create_collection("document_collection")
    chat_collection = client.get_or_create_collection("chat_collection")
    return document_collection, chat_collection


@safeExecution
def add_to_chat_collection(ids, chat_collection, embeddings, chunks, metadata):
    # print(metadata)
    chat_collection.add(
        ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadata
    )


@safeExecution
def add_to_document_collection(document_collection, ids, embeddings, chunks, metadata):
    document_collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadata,
    )


@safeExecution
def query_chat_collection(chat_collection, query_embedding, top_k=5, condition={}):
    results = chat_collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas"],
    )
    return results


@safeExecution
def query_document_collection(
    document_collection, query_embedding, top_k=5, condition={}
):
    results = document_collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas"],
    )
    return results


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
