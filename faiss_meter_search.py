import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Paths
DB_PATH = r"C:/Users/cyqt2/Database/overhaul/databases/meters.db"
EMBEDDING_MODEL_PATH = r"C:/Users/cyqt2/Database/overhaul/jina_reranker/minilm-embedding"
FAISS_INDEX_PATH = r"C:/Users/cyqt2/Database/overhaul/faiss_index.idx"
FAISS_META_PATH = r"C:/Users/cyqt2/Database/overhaul/faiss_metadata.pkl"

# 1. Build and save FAISS index from meter database
def build_faiss_index():
    import sqlite3
    model = SentenceTransformer(EMBEDDING_MODEL_PATH)
    documents = []
    metadatas = []
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = """
        SELECT id, series_name, model_name, product_name, selection_blurb FROM Meters
        ORDER BY series_name, model_name
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            meter_id, series_name, model_name, product_name, selection_blurb = row
            doc = f"Model: {model_name}\nSeries: {series_name}\nProduct: {product_name}\nDescription: {selection_blurb}"
            documents.append(doc)
            metadatas.append({
                'meter_id': meter_id,
                'model_name': model_name,
                'series_name': series_name,
                'product_name': product_name,
                'selection_blurb': selection_blurb
            })
    print(f"Embedding {len(documents)} documents...")
    embeddings = model.encode(documents, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(FAISS_META_PATH, 'wb') as f:
        pickle.dump({'metadatas': metadatas, 'documents': documents}, f)
    print(f"FAISS index and metadata saved.")

# 2. Query FAISS index
def query_faiss(query_text, top_k=3):
    model = SentenceTransformer(EMBEDDING_MODEL_PATH)
    index = faiss.read_index(FAISS_INDEX_PATH)
    with open(FAISS_META_PATH, 'rb') as f:
        meta = pickle.load(f)
    query_emb = model.encode([query_text], convert_to_numpy=True)
    D, I = index.search(query_emb, top_k)
    results = []
    for idx in I[0]:
        if idx < len(meta['metadatas']):
            results.append({
                'metadata': meta['metadatas'][idx],
                'document': meta['documents'][idx]
            })
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FAISS Meter Semantic Search")
    parser.add_argument('--build', action='store_true', help='Build FAISS index from database')
    parser.add_argument('--query', type=str, help='Query string for semantic search')
    parser.add_argument('--top_k', type=int, default=3, help='Number of results to return')
    args = parser.parse_args()

    if args.build:
        build_faiss_index()
    elif args.query:
        results = query_faiss(args.query, top_k=args.top_k)
        print(f"Top {args.top_k} results for query: '{args.query}'\n")
        for i, r in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Model: {r['metadata']['model_name']}")
            print(f"  Series: {r['metadata']['series_name']}")
            print(f"  Product: {r['metadata']['product_name']}")
            print(f"  Description: {r['metadata']['selection_blurb']}")
            print(f"  Document: {r['document'][:200]}...")
            print()
    else:
        print("Specify --build to build the index or --query 'your text' to search.")
