from llama_index.core import SQLDatabase, Settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from .database_context_provider import DatabaseContextProvider
import asyncio
from sqlalchemy import create_engine

class LlamaIndexQueryEngine:
    def __init__(self, db_path, llm_model="qwen2.5-coder:7b-instruct", smart_wrapper=None):
        self.db_path = db_path
        self.smart_wrapper = smart_wrapper
        
        # Configure LLM with standard settings
        self.llm = Ollama(
            model=llm_model,
            request_timeout=300.0,
            temperature=0.0
        )
        
        # Configure embeddings
        # Use Qwen3-Embedding-4B:Q4_K_M (quantized) via HuggingFaceEmbedding or custom loader
        self.embed_model = HuggingFaceEmbedding(
            model_name="dengcao/Qwen3-Embedding-4B:Q4_K_M"
        )
        
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Create SQL database
        engine = create_engine(f"sqlite:///{db_path}")
        self.sql_database = SQLDatabase(engine)
        
        # Create query engine
        self.query_engine = NLSQLTableQueryEngine(
            sql_database=self.sql_database,
            llm=self.llm,
            embed_model=self.embed_model,
            verbose=True,
            synthesize_response=True
        )
        
        # Get context provider for dynamic context
        self.context_provider = DatabaseContextProvider(db_path)
        
        print("🔧 LlamaIndex initialized")

    async def query(self, natural_language_query: str, additional_context: dict = None) -> str:
        print(f"🦙 LlamaIndex NL Query: {natural_language_query}")
        
        # Get database context
        db_context = self.context_provider.format_context_for_llm()
        
        # Create enhanced query
        enhanced_query = f"""
{db_context}

CRITICAL INSTRUCTIONS:
1. Generate appropriate SQL query for the user's request
2. Execute the SQL query against the database
3. Return the ACTUAL results from the database
4. Do NOT return examples, samples, or placeholder data

USER QUERY: {natural_language_query}

Execute the query and return actual database results.
        """
        
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self.query_engine.query, enhanced_query),
                timeout=300
            )
            return str(result)
        except Exception as e:
            print(f"❌ Query error: {e}")
            return f"Query failed: {str(e)}"