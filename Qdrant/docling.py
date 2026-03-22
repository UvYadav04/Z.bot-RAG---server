# from docling.document_converter import DocumentConverter
# from docling.chunking import HybridChunker
from utils.safeExecution import safeExecution
import os

# env = os.getenv("ENV", "DEVELOPMENT")

# converter = DocumentConverter()


# @safeExecution
# def parse_doc(doc):
#     result = converter.convert(doc)
#     document = result.document
#     return document


# @safeExecution
# def chunkDocs(doc, tokenizer):

#     chunker = HybridChunker(tokenizer=tokenizer, max_tokens=512, merge_peers=True)

#     chunks = chunker.chunk(dl_doc=doc)
#     return list(chunks)


from pdf_chunker_for_rag import CleanHybridPDFChunker

# Initialize the production chunker
chunker = CleanHybridPDFChunker()

def chunk_text_manual(path, chunk_size=500, overlap=100):
    # Process PDF with strategic header chunking
    chunks = chunker.strategic_header_chunking(
        pdf_path=path, target_words_per_chunk=chunk_size
    )
    return chunks


def get_embedding(text,client):
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


@safeExecution
def encodeChunksManual(chunks,client):
    embeddings = [get_embedding(chunk,client) for chunk in chunks]
    return embeddings


# @safeExecution
# def encodeChunks(chunks):
#     chunk_texts = [chunk.text for chunk in chunks]
#     embeddings = embedding_model.encode(chunk_texts, batch_size=4)
#     return embeddings
