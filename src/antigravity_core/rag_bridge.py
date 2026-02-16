# src/antigravity_core/rag_bridge.py — V4.0 Hybrid Search (Vector + Lexical)
import sqlite3
import re
import time
import chromadb
from rank_bm25 import BM25Okapi
from typing import List, Dict

MAX_RETRIES = 3
RETRY_DELAY = 0.5
DB_PATH = "./kaggle_rag_db"

class TrinityRAG:
    def __init__(self, kb_path: str = 'trinity_kb.db', aimo_path: str = 'trinity_aimo.db'):
        self.kb_path = kb_path
        self.aimo_path = aimo_path
        
        # Initialize Matrix (Vector DB)
        try:
            self.chroma_client = chromadb.PersistentClient(path=DB_PATH)
            self.vector_text = self.chroma_client.get_collection("kaggle_text")
            self.vector_code = self.chroma_client.get_collection("kaggle_code")
            print("🧩 Matrix (Vector DB) Connected.")
        except Exception as e:
            print(f"⚠️ Vector DB connection failed: {e}")
            self.chroma_client = None
            
        # H3: Vector DB Metrics
        self.metrics = {
            "vector_retrieval_success": 0,
            "vector_retrieval_failed": 0,
            "fallback_trigger_count": 0
        }

    def retrieve(self, query: str, limit: int = 3, source: str = "ALL") -> List[Dict]:
        """
        Hybrid Retrieval: Combines Vector (Semantic) and BM25 (Keyword) search.
        """
        results = {}

        # 1. Vector Search (Semantic)
        if self.chroma_client:
            try:
                # Query Text Collection
                v_results = self.vector_text.query(query_texts=[query], n_results=limit)
                for i, doc_id in enumerate(v_results['ids'][0]):
                    content = v_results['documents'][0][i]
                    meta = v_results['metadatas'][0][i]
                    dist = v_results['distances'][0][i]
                    
                    # Normalize distance to score (0-1)
                    score = 1.0 / (1.0 + dist)
                    
                    results[doc_id] = {
                        'id': doc_id,
                        'content': content,
                        'type': 'vector_match',
                        'score': score * 1.2, # Boost vector results slightly
                        'source': 'matrix'
                    }
                self.metrics["vector_retrieval_success"] += 1
            except Exception as e:
                print(f"⚠️ Vector retrieval error: {e}")
                self.metrics["vector_retrieval_failed"] += 1
                self.metrics["fallback_trigger_count"] += 1
        else:
             self.metrics["fallback_trigger_count"] += 1

        # 2. Keyword Search (BM25 from SQLite)
        if source in ["ALL", "STRATEGIC"]:
            conn = None
            try:
                conn = sqlite3.connect(self.kb_path)
                c = conn.cursor()
                c.execute('SELECT id, filename, content, type FROM kb')
                docs = c.fetchall()
                
                if docs:
                    texts = [doc[2] for doc in docs]
                    tokenized = [self._tokenize(t) for t in texts]
                    bm25 = BM25Okapi(tokenized)
                    scores = bm25.get_scores(self._tokenize(query))
                    
                    ranked = sorted(zip(range(len(docs)), scores), key=lambda x: x[1], reverse=True)
                    for idx, score in ranked[:limit]:
                        if score < 0.1: continue # Filter low quality
                        
                        doc = docs[idx]
                        doc_id = f"kb_{doc[0]}"
                        
                        # Merge or Add
                        if doc_id in results:
                            results[doc_id]['score'] += score
                            results[doc_id]['source'] = 'hybrid'
                        else:
                            results[doc_id] = {
                                'id': doc_id,
                                'content': doc[2],
                                'type': doc[3],
                                'score': score,
                                'source': 'lexical'
                            }
            except Exception as e:
                print(f"⚠️ BM25 retrieval error: {e}")
            finally:
                if conn: conn.close()

        # Sort by final score
        final_results = sorted(results.values(), key=lambda x: x['score'], reverse=True)
        
        # Log Metrics
        print(f"📊 RAG Metrics: Vector Success={self.metrics['vector_retrieval_success']} | "
              f"Failed={self.metrics['vector_retrieval_failed']} | "
              f"Fallback={self.metrics['fallback_trigger_count']}")
              
        return final_results[:limit]
    
    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())
    
    def format_for_prompt(self, results: List[Dict]) -> str:
        if not results:
            return "No relevant institutional memory found."
        
        formatted = "### INSTITUTIONAL MEMORY (Hybrid) ###\n"
        for i, doc in enumerate(results, 1):
            src = doc.get('source', 'unknown')
            formatted += f"\n**Memory {i}** [{src.upper()} - Score: {doc['score']:.2f}]:\n{doc.get('content', '')[:600]}\n"
        
        return formatted
    
    def save(self, filename: str, content: str, doc_type: str = "note"):
        """Save a document to trinity_kb.db with transactional retry (3x)."""
        for attempt in range(1, MAX_RETRIES + 1):
            conn = None
            try:
                conn = sqlite3.connect(self.kb_path)
                conn.execute("BEGIN")
                conn.execute('INSERT INTO kb (filename, content, type) VALUES (?, ?, ?)', (filename, content, doc_type))
                conn.commit()
                print(f"✅ Saved: {filename}")
                return True
            except sqlite3.IntegrityError:
                if conn: conn.rollback()
                return self.upsert(filename, content, doc_type)
            except Exception as e:
                if conn: conn.rollback()
                print(f"⚠️ Save attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES: time.sleep(RETRY_DELAY * attempt)
            finally:
                if conn: conn.close()
        return False

    def upsert(self, filename: str, content: str, doc_type: str = "note"):
        for attempt in range(1, MAX_RETRIES + 1):
            conn = None
            try:
                conn = sqlite3.connect(self.kb_path)
                conn.execute("BEGIN")
                conn.execute('INSERT OR REPLACE INTO kb (filename, content, type) VALUES (?, ?, ?)', (filename, content, doc_type))
                conn.commit()
                print(f"✅ Upserted: {filename}")
                return True
            except Exception as e:
                if conn: conn.rollback()
                print(f"⚠️ Upsert attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES: time.sleep(RETRY_DELAY * attempt)
            finally:
                if conn: conn.close()
        return False

if __name__ == "__main__":
    rag = TrinityRAG()
    results = rag.retrieve("generic pipeline stability", limit=3)
    print(rag.format_for_prompt(results))
