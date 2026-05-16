import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

def setup_pinecone():
    load_dotenv()
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "enterprise-rag-index")
    
    if not api_key:
        print("Error: PINECONE_API_KEY not found in .env file.")
        return

    print(f"Connecting to Pinecone...")
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if index_name in existing_indexes:
        print(f"Index '{index_name}' already exists.")
    else:
        print(f"Creating index '{index_name}'...")
        try:
            pc.create_index(
                name=index_name,
                dimension=3072, # Dimension for gemini-embedding-001
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"Index creation initiated. Waiting for index to be ready...")
            
            # Wait for index to be ready
            while not pc.describe_index(index_name).status['ready']:
                time.sleep(1)
            
            print(f"Index '{index_name}' is now ready.")
        except Exception as e:
            print(f"Error creating index: {e}")

if __name__ == "__main__":
    setup_pinecone()
