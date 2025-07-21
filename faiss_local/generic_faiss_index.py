import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

class GenericFAISSIndex:
    def __init__(self, db_path, embedding_model_path, index_dir):
        self.db_path = db_path
        self.embedding_model_path = embedding_model_path
        self.index_dir = index_dir
        self.index_path = os.path.join(index_dir, 'faiss_index.idx')
        self.meta_path = os.path.join(index_dir, 'faiss_metadata.pkl')
        os.makedirs(index_dir, exist_ok=True)

    def build_index(self, sql_query, doc_builder, meta_builder):
        import sqlite3
        model = SentenceTransformer(self.embedding_model_path)
        documents = []
        metadatas = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            for row in cursor.fetchall():
                documents.append(doc_builder(row))
                metadatas.append(meta_builder(row))
        print(f"Embedding {len(documents)} documents...")
        embeddings = model.encode(documents, show_progress_bar=True, convert_to_numpy=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        faiss.write_index(index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump({'metadatas': metadatas, 'documents': documents}, f)
        print(f"FAISS index and metadata saved to {self.index_dir}.")

    def query(self, query_text, top_k=3):
        if not (os.path.exists(self.index_path) and os.path.exists(self.meta_path)):
            raise RuntimeError(f"FAISS index or metadata missing in {self.index_dir}. Please build the index first.")
        model = SentenceTransformer(self.embedding_model_path)
        index = faiss.read_index(self.index_path)
        with open(self.meta_path, 'rb') as f:
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
