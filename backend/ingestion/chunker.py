from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks the document text and attaches the provided metadata to each chunk.
        """
        chunks = self.text_splitter.split_text(text)
        chunked_documents = []
        for i, chunk in enumerate(chunks):
            # Create a copy of the metadata for each chunk and add chunk-specific info
            chunk_meta = metadata.copy()
            chunk_meta["chunk_id"] = f"{metadata.get('filename', 'doc')}_chunk_{i}"
            chunk_meta["text"] = chunk # Store text in metadata for Pinecone retrieval
            
            chunked_documents.append({
                "page_content": chunk,
                "metadata": chunk_meta
            })
            
        return chunked_documents
