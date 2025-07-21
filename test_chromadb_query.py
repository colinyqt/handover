import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Path to your ChromaDB collection
CHROMA_COLLECTION_PATH = r'C:/Users/cyqt2/Database/overhaul/chroma_db/meters'
# Path to your local embedding model
EMBEDDING_MODEL_PATH = r'C:\Users\cyqt2\Database\overhaul\jina_reranker\minilm-embedding'

# Example queries to test
TEST_QUERIES = [
    "Accuracy class 0.5 or better",
    "RS485 communication",
    "True RMS Current ±0.5%",
    "Harmonics up to 31st order",
    "On-board memory up to 8 GB"
]

def main():
    print(f"Loading embedding model from: {EMBEDDING_MODEL_PATH}")
    embedder = SentenceTransformer(EMBEDDING_MODEL_PATH)

    print(f"Connecting to ChromaDB collection at: {CHROMA_COLLECTION_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_COLLECTION_PATH, settings=Settings(allow_reset=True))
    collection = client.get_or_create_collection("meters_semantic")

    for query in TEST_QUERIES:
        print(f"\nQuery: {query}")
        embedding = embedder.encode([query]).tolist()
        results = collection.query(
            query_embeddings=embedding,
            n_results=5,
            include=['metadatas', 'distances', 'documents']
        )
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                print(f"  Result {i+1}: {doc}")
                if results['metadatas']:
                    print(f"    Metadata: {results['metadatas'][0][i]}")
                if results['distances']:
                    print(f"    Distance: {results['distances'][0][i]}")
        else:
            print("  No results found.")

    # Run a test query without embeddings
    query_texts = ["Real Power", "Frequency", "RS485 communication"]
    results = collection.query(query_texts=query_texts, n_results=3)

    for idx, q in enumerate(query_texts):
        docs = results['documents'][idx]
        print(f"Query '{q}' -> {len(docs)} results")
        for i, doc in enumerate(docs):
            print(f"  {i+1}. {doc[:150]}...")

if __name__ == "__main__":
    main()
