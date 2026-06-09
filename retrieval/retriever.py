"""
retriever.py — Finds the most relevant document chunks for a user's question.

How it works:
  1. User asks: "What is polymorphism?"
  2. The query rewriter (an LLM) generates 3 alternative search queries
     to improve recall (e.g., "define polymorphism", "polymorphism in OOP")
  3. All queries are searched against ChromaDB using MMR (Maximal Marginal Relevance)
  4. Results are deduplicated and returned
"""

import re
from llm.prompt import load_query_rewriter_prompt


class RoutedRetriever:
    """Retrieves relevant document chunks with LLM-powered query expansion."""

    def __init__(self, vectorstore, router=None):
        self.base_retriever = vectorstore.as_retriever(
            search_type="mmr",  # MMR = balances relevance with diversity
            search_kwargs={
                "k": 4,             # Return top 4 results (reduced from 6 to save tokens)
                "fetch_k": 20,       # Consider top 20 candidates before filtering
                "lambda_mult": 0.7,  # 0.0 = max diversity, 1.0 = max relevance
            },
        )
        self.router = router  # The AI model router (for query rewriting)

    def invoke(self, query: str, chat_history: str = ""):
        """Search for documents relevant to the query.

        If a router is available, the query is first rewritten into multiple
        variations to catch more relevant chunks.
        """
        search_queries = [query]

        # Expand the query into 3 alternative versions using AI
        if self.router is not None:
            search_queries.extend(self._rewrite_query(query, chat_history))

        # Search with each query concurrently and deduplicate results
        import concurrent.futures
        seen = set()
        documents = []
        
        def fetch_docs(sq):
            return self.base_retriever.invoke(sq)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_query = {executor.submit(fetch_docs, sq): sq for sq in search_queries}
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    docs = future.result()
                    for doc in docs:
                        doc_key = (doc.page_content, tuple(sorted(doc.metadata.items())))
                        if doc_key not in seen:
                            seen.add(doc_key)
                            documents.append(doc)
                except Exception as exc:
                    print(f"Search query failed: {exc}")

        return documents

    def _rewrite_query(self, query: str, chat_history: str = "") -> list[str]:
        """Use an LLM to generate alternative search queries."""
        prompt = load_query_rewriter_prompt()
        raw_response = self.router.complete(
            "query_rewriting",
            [{"role": "user", "content": prompt.format(query=query, chat_history=chat_history)}],
            temperature=0.0,
        )

        # Parse the response — one query per line, clean up numbering
        rewrites = []
        for line in raw_response.splitlines():
            cleaned = re.sub(r"^[\-\d\.\)\s]+", "", line).strip()
            if cleaned and cleaned.lower() != query.lower():
                rewrites.append(cleaned)

        return rewrites[:3]  # Keep at most 3 rewrites


def create_retriever(vectorstore, router=None):
    """Factory function — creates a RoutedRetriever instance."""
    return RoutedRetriever(vectorstore, router)
