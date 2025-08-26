# services/rag_service.py
import os
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from db.database import weaviate_client

# Import from the correct v4 locations
import weaviate.classes.config as wvc
from weaviate.classes.query import Filter  # <-- CORRECT IMPORT LOCATION FOR FILTER
from weaviate.util import generate_uuid5

embeddings_model = OpenAIEmbeddings()
COLLECTION_NAME = "DocumentChunk"

def create_weaviate_schema():
    if not weaviate_client.collections.exists(COLLECTION_NAME):
        weaviate_client.collections.create(
            name=COLLECTION_NAME,
            # Use the updated 'vector_config' parameter name
            vector_config=wvc.Configure.VectorIndex.hnsw(), 
            properties=[
                wvc.Property(name="content", data_type=wvc.DataType.TEXT),
                wvc.Property(name="user_id", data_type=wvc.DataType.UUID),
                wvc.Property(name="file_id", data_type=wvc.DataType.UUID),
            ]
        )

def process_and_embed_file(file_path: str, user_id: uuid.UUID, file_id: uuid.UUID):
    # Load PDF documents
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # Optimized chunking: larger chunks for fewer API calls
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,  # Increased from 1000
        chunk_overlap=300,  # Increased from 150 for better context
        separators=["\n\n", "\n", ". ", " ", ""]  # Prioritize paragraph breaks
    )
    chunks = text_splitter.split_documents(documents)

    doc_chunks = weaviate_client.collections.get(COLLECTION_NAME)

    # Batch processing for embeddings - collect all texts first
    texts_to_embed = [chunk.page_content for chunk in chunks]

    # Batch embed all texts at once (more efficient)
    if texts_to_embed:
        vectors = embeddings_model.embed_documents(texts_to_embed)

        # Batch insert into Weaviate
        with doc_chunks.batch.dynamic() as batch:
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                data_object = {
                    "content": chunk.page_content,
                    "user_id": user_id,
                    "file_id": file_id,
                }

                batch.add_object(
                    properties=data_object,
                    vector=vector,
                    uuid=generate_uuid5(data_object)
                )

    return len(chunks)

def query_weaviate(query: str, user_id: uuid.UUID, file_ids: list[uuid.UUID]):
    query_vector = embeddings_model.embed_query(query)
    doc_chunks = weaviate_client.collections.get(COLLECTION_NAME)

    # Convert UUIDs to strings for the filter
    file_id_strs = [str(fid) for fid in file_ids]

    response = doc_chunks.query.near_vector(
        near_vector=query_vector,
        # Filter by user AND the specific files in the session
        filters=(
            Filter.by_property("user_id").equal(user_id) &
            Filter.by_property("file_id").contains_any(file_id_strs)
        ),
        limit=3,
        return_properties=["content"]
    )

    return [obj.properties for obj in response.objects]
