from transformers import AutoModel, AutoTokenizer
from sentence_transformers import CrossEncoder, SentenceTransformer

# Download embedding model (MiniLM)
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embedding_model.save('./jina_reranker/minilm-embedding')

# Download reranker model (CrossEncoder)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
reranker.save_pretrained('./jina_reranker/cross-encoder')
tokenizer = AutoTokenizer.from_pretrained('cross-encoder/ms-marco-MiniLM-L-6-v2')
tokenizer.save_pretrained('./jina_reranker/cross-encoder')