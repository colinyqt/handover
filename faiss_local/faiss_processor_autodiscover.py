import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer

def discover_faiss_indexes(index_dir):
    """Return a list of FAISS index and metadata file pairs in the given directory."""
    index_files = []
    for fname in os.listdir(index_dir):
        if fname.endswith('.idx'):
            base = fname[:-4]
            meta = os.path.join(index_dir, base + '.pkl')
            idx = os.path.join(index_dir, fname)
            if os.path.exists(meta):
                index_files.append((idx, meta))
    return index_files

def load_faiss_index(index_path, meta_path):
    index = faiss.read_index(index_path)
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)
    return index, meta

def query_all_indexes(query_text, index_dir, embedding_model_path, top_k=3):
    model = SentenceTransformer(embedding_model_path)
    query_emb = model.encode([query_text], convert_to_numpy=True)
    results = []
    for idx_path, meta_path in discover_faiss_indexes(index_dir):
        index, meta = load_faiss_index(idx_path, meta_path)
        D, I = index.search(query_emb, top_k)
        for idx in I[0]:
            if idx < len(meta['metadatas']):
                results.append({
                    'index': idx_path,
                    'metadata': meta['metadatas'][idx],
                    'document': meta['documents'][idx]
                })
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FAISS Index Autodiscovery Search")
    parser.add_argument('--query', type=str, help='Query string for semantic search')
    parser.add_argument('--index_dir', type=str, default='faiss_indexes', help='Directory to search for FAISS indexes')
    parser.add_argument('--embedding_model', type=str, default='jina_reranker/minilm-embedding', help='Embedding model path')
    parser.add_argument('--top_k', type=int, default=3, help='Number of results to return per index')
    args = parser.parse_args()

    if args.query:
        results = query_all_indexes(args.query, args.index_dir, args.embedding_model, top_k=args.top_k)
        for i, r in enumerate(results):
            print(f"Result {i+1} from {r['index']}")
            print(f"  Model: {r['metadata'].get('model_name')}")
            print(f"  Series: {r['metadata'].get('series_name')}")
            print(f"  Product: {r['metadata'].get('product_name')}")
            print(f"  Description: {r['metadata'].get('selection_blurb')}")
            print(f"  Document: {r['document'][:200]}...")
            print()
    else:
        print("Specify --query 'your text' to search all FAISS indexes in the directory.")
