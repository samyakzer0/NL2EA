from dotenv import load_dotenv

load_dotenv(".env.local", override=True)

import os
from sqlalchemy.engine import make_url

url = make_url(os.environ["DATABASE_URL"])
print(f"INGEST DATABASE: {url.host}:{url.port}/{url.database}")

import hashlib
from pathlib import Path
from ingestion.document_loader import load_documents
from ingestion.chunker import chunk_documents
from retrieval.vector_store import create_vector_store


def generate_chunk_id(chunk):
    source = chunk.metadata["file_path"]

    start_index = chunk.metadata.get("start_index", 0)

    content_hash =hashlib.sha256(chunk.page_content.encode("utf-8")).hexdigest()

    unique_value = f"{source}:{start_index}:{content_hash}"

    return hashlib.sha256(unique_value.encode("utf-8")).hexdigest()


def ingest_documents(directory):
    documents = load_documents(directory)

    if not documents:
        raise ValueError(f"No supported documents found in {directory}")

    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError(f"No chunks created from documents in {directory}")

    vector_store = create_vector_store()

    chunk_ids=[
        generate_chunk_id(chunk)
        for chunk in chunks
    ]


    vector_store.add_documents(documents=chunks, ids=chunk_ids)

    print(f"Successfully ingested {len(chunks)} chunks into the vector store.")
    print(f"Successfully ingested {len(documents)} documents into the vector store.")

    return len(chunks)


if __name__ == "__main__":
    ingest_documents(Path("zer0Labs"))
