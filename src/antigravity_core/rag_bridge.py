# src/antigravity_core/rag_bridge.py — V3.14 Transactional Inserts
import sqlite3
import re
import time
from rank_bm25 import BM25Okapi
from typing import List, Dict

MAX_RETRIES = 3
RETRY_DELAY = 0.5


class TrinityRAG:
    def __init__(self, kb_path: str = 'trinity_kb.db', aimo_path: str = 'trinity_aimo.db'):
        self.kb_path = kb_path
        self.aimo_path = aimo_path
    
    def retrieve(self, query: str, limit: int = 2, source: str = "ALL") -> List[Dict]:
        """
        Retrieve relevant documents from KB.
        Sources: ALL, STRATEGIC (trinity_kb), TACTICAL (trinity_aimo)
        """
        results = []
        
        # Query trinity_kb.db (Strategic)
        if source in ["ALL", "STRATEGIC"]:
            conn = None
            try:
                conn = sqlite3.connect(self.kb_path)
                c = conn.cursor()
                
                # Get all docs — schema: id, filename, content, type
                c.execute('SELECT id, filename, content, type FROM kb')
                docs = c.fetchall()
                
                if docs:
                    # BM25 ranking
                    texts = [doc[2] for doc in docs]  # content column
                    tokenized = [self._tokenize(t) for t in texts]
                    bm25 = BM25Okapi(tokenized)
                    
                    query_tokens = self._tokenize(query)
                    scores = bm25.get_scores(query_tokens)
                    
                    # Top results
                    ranked = sorted(zip(range(len(docs)), scores), key=lambda x: x[1], reverse=True)
                    for idx, score in ranked[:limit]:
                        doc = docs[idx]
                        results.append({
                            'id': doc[0],
                            'filename': doc[1],
                            'content': doc[2],
                            'type': doc[3],
                            'score': score
                        })
            except Exception as e:
                print(f"⚠️ KB retrieval error: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Query trinity_aimo.db (Tactical)
        if source in ["ALL", "TACTICAL"]:
            conn = None
            try:
                conn = sqlite3.connect(self.aimo_path)
                c = conn.cursor()
                
                c.execute('SELECT id, problem_id, code, success FROM aimo_history WHERE success=1 ORDER BY id DESC LIMIT 5')
                successes = c.fetchall()
                
                for doc in successes:
                    results.append({
                        'id': doc[0],
                        'problem_id': doc[1],
                        'code': doc[2],
                        'type': 'solution',
                        'score': 1.0
                    })
            except Exception as e:
                print(f"⚠️ AIMO retrieval error: {e}")
            finally:
                if conn:
                    conn.close()
        
        return results[:limit]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return re.findall(r'\w+', text.lower())
    
    def format_for_prompt(self, results: List[Dict]) -> str:
        """Format retrieval results for LLM prompt."""
        if not results:
            return "No relevant institutional memory found."
        
        formatted = "### INSTITUTIONAL MEMORY ###\n"
        for i, doc in enumerate(results, 1):
            if doc['type'] == 'solution':
                formatted += f"\n**Solution {i}** (Problem {doc.get('problem_id', '?')}):\n{doc.get('code', '')}\\n"
            else:
                formatted += f"\n**Document {i}** ({doc['type']}):\n{doc.get('content', '')[:500]}\n"
        
        return formatted
    
    def save(self, filename: str, content: str, doc_type: str = "note"):
        """Save a document to trinity_kb.db with transactional retry (3x)."""
        for attempt in range(1, MAX_RETRIES + 1):
            conn = None
            try:
                conn = sqlite3.connect(self.kb_path)
                conn.execute("BEGIN")
                conn.execute('''
                    INSERT INTO kb (filename, content, type)
                    VALUES (?, ?, ?)
                ''', (filename, content, doc_type))
                conn.commit()
                print(f"✅ Saved: {filename}")
                return True
            except sqlite3.IntegrityError:
                # Filename already exists (UNIQUE constraint) — use upsert
                if conn:
                    conn.rollback()
                return self.upsert(filename, content, doc_type)
            except Exception as e:
                if conn:
                    conn.rollback()
                print(f"⚠️ Save attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
            finally:
                if conn:
                    conn.close()
        print(f"❌ Save failed after {MAX_RETRIES} attempts: {filename}")
        return False

    def upsert(self, filename: str, content: str, doc_type: str = "note"):
        """Upsert (INSERT OR REPLACE) a document. Idempotent save."""
        for attempt in range(1, MAX_RETRIES + 1):
            conn = None
            try:
                conn = sqlite3.connect(self.kb_path)
                conn.execute("BEGIN")
                conn.execute('''
                    INSERT OR REPLACE INTO kb (filename, content, type)
                    VALUES (?, ?, ?)
                ''', (filename, content, doc_type))
                conn.commit()
                print(f"✅ Upserted: {filename}")
                return True
            except Exception as e:
                if conn:
                    conn.rollback()
                print(f"⚠️ Upsert attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
            finally:
                if conn:
                    conn.close()
        print(f"❌ Upsert failed after {MAX_RETRIES} attempts: {filename}")
        return False


if __name__ == "__main__":
    rag = TrinityRAG()
    results = rag.retrieve("heart disease xgboost", limit=2)
    print(rag.format_for_prompt(results))
