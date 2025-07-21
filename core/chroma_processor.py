import chromadb
from typing import Dict, List, Any
import json
import re
from jinja2 import Template

class ChromaProcessor:
    def query_chromadb(self, query: str, top_k: int = 3, collection_name: str = None) -> list:
        """Direct embedding-based ChromaDB search for use in native Python pipeline steps."""
        # Use the first collection if not specified
        if not collection_name:
            if self.collections:
                collection_name = list(self.collections.keys())[0]
            else:
                print("[ERROR] No Chroma collections available.")
                return []
        if collection_name not in self.collections:
            print(f"[ERROR] Collection '{collection_name}' not found in ChromaProcessor.")
            return []
        collection = self.collections[collection_name]
        try:
            if self.embedder:
                embedding = self.embedder.encode([query]).tolist()
                query_results = collection.query(
                    query_embeddings=embedding,
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )
            else:
                # Fallback to text query if embedder not available
                query_results = collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )
            docs = query_results.get("documents", [[]])[0]
            metadatas = query_results.get("metadatas", [[]])[0] if "metadatas" in query_results else [{}]*len(docs)
            results = []
            for i, doc in enumerate(docs):
                result = {"text": doc}
                if metadatas and i < len(metadatas):
                    result["metadata"] = metadatas[i]
                results.append(result)
            print(f"[DEBUG] query_chromadb('{query}') returned {len(results)} results from '{collection_name}'")
            return results
        except Exception as e:
            print(f"[ERROR] query_chromadb failed for '{query}': {e}")
            return []
    def __init__(self, chroma_config: Dict[str, str], embedding_model_path: str = r'C:\Users\cyqt2\Database\overhaul\jina_reranker\minilm-embedding'):
        self.collections = {}
        self.clients = {}
        self.embedding_model_path = embedding_model_path
        # Load embedding model once
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer(self.embedding_model_path)
            print(f"✅ Loaded embedding model from: {self.embedding_model_path}")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            self.embedder = None
        # Initialize Chroma collections from YAML config
        for collection_name, db_path in chroma_config.items():
            try:
                client = chromadb.PersistentClient(path=db_path)
                self.clients[collection_name] = client
                self.collections[collection_name] = client.get_or_create_collection(collection_name)
                print(f"✅ Chroma collection '{collection_name}' initialized at {db_path}")
            except Exception as e:
                print(f"❌ Failed to initialize Chroma collection '{collection_name}': {e}")
    
    async def process_chroma_step(self, step_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Chroma step from YAML configuration"""
        collection_name = step_config.get('collection')
        if collection_name not in self.collections:
            return {'success': False, 'error': f'Collection {collection_name} not found'}
        collection = self.collections[collection_name]

        # Use structured requirements if available, else fallback to extracting from prompt
        requirements = context.get('requirements')
        results = {}
        total_queries = 0
        if requirements and isinstance(requirements, list) and all(isinstance(r, dict) for r in requirements):
            # For each clause, query Chroma for each atomic feature using embeddings
            for clause in requirements:
                clause_title = clause.get('clause', 'Unknown Clause')
                features = clause.get('features', [])
                clause_results = {}
                for feature in features:
                    search_params = step_config.get('search_params', {})
                    try:
                        if self.embedder:
                            embedding = self.embedder.encode([feature]).tolist()
                            query_results = collection.query(
                                query_embeddings=embedding,
                                n_results=search_params.get('n_results', 5),
                                include=['metadatas', 'documents', 'distances'] if search_params.get('include_metadata') else ['documents']
                            )
                        else:
                            # Fallback to text query if embedder not available
                            query_results = collection.query(
                                query_texts=[feature],
                                n_results=search_params.get('n_results', 5),
                                include=['metadatas', 'documents', 'distances'] if search_params.get('include_metadata') else ['documents']
                            )
                        candidates = []
                        docs = query_results.get('documents', [[]])[0]
                        metadatas = query_results.get('metadatas', [[]])[0] if 'metadatas' in query_results else [{}]*len(docs)
                        for i, doc in enumerate(docs):
                            candidate = {'text': doc}
                            if metadatas and i < len(metadatas):
                                candidate['metadata'] = metadatas[i]
                            candidates.append(candidate)
                        clause_results[feature] = candidates
                        print(f"🔍 Chroma search for clause '{clause_title}' feature '{feature}': {len(candidates)} results")
                        total_queries += 1
                    except Exception as e:
                        print(f"❌ Chroma search failed for clause '{clause_title}' feature '{feature}': {e}")
                        clause_results[feature] = [{'text': '', 'metadata': {}, 'error': str(e)}]
                        total_queries += 1
                results[clause_title] = clause_results
        else:
            # Fallback: old logic, but use embeddings if available
            search_queries = []
            if requirements and isinstance(requirements, list):
                search_queries = [str(r) for r in requirements if r]
            if not search_queries:
                prompt = self.render_template(step_config['prompt_template'], context)
                search_queries = self.extract_search_queries(prompt)
            if not search_queries:
                return {'success': False, 'error': 'No search queries found in requirements or prompt'}
            for query in search_queries:
                search_params = step_config.get('search_params', {})
                try:
                    if self.embedder:
                        embedding = self.embedder.encode([query]).tolist()
                        query_results = collection.query(
                            query_embeddings=embedding,
                            n_results=search_params.get('n_results', 5),
                            include=['metadatas', 'documents', 'distances'] if search_params.get('include_metadata') else ['documents']
                        )
                    else:
                        query_results = collection.query(
                            query_texts=[query],
                            n_results=search_params.get('n_results', 5),
                            include=['metadatas', 'documents', 'distances'] if search_params.get('include_metadata') else ['documents']
                        )
                    candidates = []
                    docs = query_results.get('documents', [[]])[0]
                    metadatas = query_results.get('metadatas', [[]])[0] if 'metadatas' in query_results else [{}]*len(docs)
                    for i, doc in enumerate(docs):
                        candidate = {'text': doc}
                        if metadatas and i < len(metadatas):
                            candidate['metadata'] = metadatas[i]
                        candidates.append(candidate)
                    results[query] = candidates
                    print(f"🔍 Chroma search for '{query}': {len(candidates)} results")
                    total_queries += 1
                except Exception as e:
                    print(f"❌ Chroma search failed for '{query}': {e}")
                    results[query] = [{'text': '', 'metadata': {}, 'error': str(e)}]
                    total_queries += 1

        return {
            'success': True,
            'results': results,
            'collection': collection_name,
            'total_queries': total_queries
        }
    
    def extract_search_queries(self, prompt: str) -> List[str]:
        """Extract search queries from rendered prompt"""
        # Look for quoted strings (like "±0.5% accuracy power measurement")
        quoted_queries = re.findall(r'"([^"]*)"', prompt)
        
        # Look for bullet points with requirements
        bullet_queries = re.findall(r'- ([^\n]*)', prompt)
        
        # Filter out empty queries
        all_queries = [q.strip() for q in quoted_queries + bullet_queries if q.strip()]
        
        return all_queries
    
    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context"""
        from jinja2 import Template
        return Template(template).render(**context)