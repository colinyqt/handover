from faiss_meter_search import query_faiss

class FAISSProcessor:
    """FAISS processor for semantic search of meter database and PDF chunks."""
    
    def __init__(self, faiss_index_path=None, metadata_path=None):
        """Initialize FAISSProcessor.
        
        Args:
            faiss_index_path: Optional path to FAISS index file for PDF chunks
            metadata_path: Optional path to metadata file for PDF chunks
        """
        self.faiss_index_path = faiss_index_path
        self.metadata_path = metadata_path
    
    def query_faiss(self, query, top_k=3):
        """Query the FAISS index with the given query string.
        
        Args:
            query: Query string to search for
            top_k: Number of top results to return
            
        Returns:
            List of search results with metadata
        """
        if self.faiss_index_path and self.metadata_path:
            # For PDF chunks, we'd use the specific index files
            # For now, fall back to the main query_faiss function
            return query_faiss(query, top_k=top_k)
        else:
            # Use the main meter database
            return query_faiss(query, top_k=top_k)
