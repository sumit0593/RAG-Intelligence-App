import os
from backend.ingestion.loader import load_document
from backend.ingestion.chunker import DocumentChunker
from backend.retrieval.pinecone_store import EnterpriseRetriever
from dotenv import load_dotenv

def index_sample_data():
    load_dotenv()
    
    file_path = "datasets/sample_policy.txt"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Loading document: {file_path}")
    text = load_document(file_path)
    
    metadata = {
        "filename": "sample_policy.txt",
        "classification": "INTERNAL",
        "department": "HR",
        "allowed_roles": ["ADMIN", "HR", "ENGINEERING"],
        "document_id": "doc_001"
    }
    
    print("Chunking document...")
    chunker = DocumentChunker()
    chunks = chunker.chunk_document(text, metadata)
    
    print(f"Indexing {len(chunks)} chunks into Pinecone...")
    retriever = EnterpriseRetriever()
    retriever.index_documents(chunks)
    print("Indexing complete.")

if __name__ == "__main__":
    index_sample_data()
