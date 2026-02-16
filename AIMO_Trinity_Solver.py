# AIMO_Trinity_Solver.py — V3.14 Production Hardening
import sqlite3
import asyncio
import ast
import re
import sys
import subprocess
import tempfile
import os
import resource
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv

load_dotenv()

from mistralai import Mistral
from src.antigravity_core.rag_bridge import TrinityRAG
import google.generativeai as genai
from collections import Counter

# ============ AST VALIDATOR ============
class SolverValidator:
    """Strict AST validator for AIMO code."""
    
    WHITELIST_LIBS = {
        'sympy', 'numpy', 'scipy', 'math', 're', 'collections', 'itertools',
        'statistics', 'fractions', 'decimal', 'bisect', 'heapq', 'copy',
        'abc', 'typing', 'functools', 'operator', 'json', 'datetime', 'time'
    }
    
    BLACKLIST_LIBS = {'os', 'subprocess', 'socket', 'requests', 'urllib', 'ftplib', 'paramiko', 'shutil', 'glob'}
    
    @staticmethod
    def validate(code: str) -> Tuple[bool, str]:
        """
        Returns (is_valid, error_message).
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"SyntaxError: {e.msg} at line {e.lineno}"
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name.split('.')[0] for alias in node.names]
                else:
                    if node.module:
                        modules = [node.module.split('.')[0]]
                
                for lib in modules:
                    if lib in SolverValidator.BLACKLIST_LIBS:
                        return False, f"VETO: Blacklisted library '{lib}' detected."
            
            elif isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                if func_name in ['exec', 'eval', 'compile', 'open', 'write', 'system', 'popen', '__import__', 'getattr']:
                    return False, f"VETO: Dangerous function '{func_name}' detected."

        return True, ""

        return True, ""

# ============ CIRCUIT BREAKER ============
import time
class CircuitBreaker:
    def __init__(self, max_failures=3, cooldown_seconds=300):
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.last_failure_time = 0

    def allow(self):
        if self.failures >= self.max_failures:
            if time.time() - self.last_failure_time < self.cooldown_seconds:
                return False
            else:
                # Cooldown expired, try again (half-open)
                return True
        return True

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

    def record_success(self):
        self.failures = 0
class TrinitySolver:
    def __init__(self):
        self.db_path = 'trinity_aimo.db'
        self.mistral = Mistral(api_key=os.getenv('MISTRAL_API_KEY', ''))
        self.rag = TrinityRAG()
        self.cb = CircuitBreaker()
        
        # Initialize Gemini for Synthesis
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY', ''))
        self.gemini = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Trinity 3-6-2 Strategy Prompts (from AIMO_Strategy_Bible.md)
        self.strategies = {
            'symbolic': 'Koristi SymPy simboličke manipulacije za rešavanje problema. Prioritizuj algebarsku preciznost nad numeričkom brzinom.',
            'brute-force': 'Koristi brute-force enumeraciju svih mogućih slučajeva. Fokusiraj se na iscrpnost rešenja.',
            'hybrid': 'Kombinuj SymPy simboliku za formulaciju problema i NumPy/SciPy za numeričku verifikaciju.',
            'alternative': 'Pronađi alternativni matematički pristup (drugačija formulacija, drugi set jednačina). Razmisli van kutije.',
            'creative': 'Primeni kreativni, inovativni pristup. Probaj nekonvencionalne matematičke tehnike.'
        }
        
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS aimo_history (
                id INTEGER PRIMARY KEY,
                problem_id INTEGER,
                problem_text TEXT,
                raw_response TEXT,
                code TEXT,
                prediction INTEGER,
                ground_truth INTEGER,
                success BOOLEAN,
                syntax_ok INTEGER DEFAULT 0,
                security_veto TEXT,
                provider TEXT,
                stdout TEXT,
                stderr TEXT,
                error_log TEXT,
                attempt INTEGER DEFAULT 1,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def _query_api(self, messages: List[dict]) -> Tuple[str, str]:
        try:
            resp = self.mistral.chat.complete(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.1,
                timeout_ms=45000
            )
            return resp.choices[0].message.content, "mistral-large"
        except Exception as e:
            print(f"⚠️ Mistral failed: {e}. Falling back to OpenRouter...")
            
            if not self.cb.allow():
                print("🛑 Circuit Breaker OPEN: Skipping OpenRouter to prevent cascade.")
                return "", "FAILED_CB"
                
            try:
                import requests
                or_key = os.getenv('OPENROUTER_API_KEY', '')
                # Fixed model ID for OpenRouter
                resp = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers={'Authorization': f'Bearer {or_key}', 'Content-Type': 'application/json'},
                    json={'model': 'deepseek/deepseek-r1', 'messages': messages, 'temperature': 0.1},
                    timeout=45
                )
                if resp.status_code == 200:
                    self.cb.record_success()
                    return resp.json()['choices'][0]['message']['content'], "openrouter/deepseek"
                print(f"❌ OpenRouter error: {resp.status_code} - {resp.text}")
                self.cb.record_failure()
                return "", "FAILED"
            except Exception as or_e:
                print(f"❌ Failover failed: {or_e}")
                self.cb.record_failure()
                return "", "FAILED"

    def extract_code(self, text: str) -> str:
        if not text: return ""
        # 1. Standard Markdown
        code_match = re.search(r'```python\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
        if code_match:
            return code_match.group(1).strip()
        
        # 2. Generic Markdown
        code_match = re.search(r'```(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        # 3. Heuristic: Look for longest indented block or import/def lines
        lines = text.split('\n')
        buffer = []
        capture = False
        
        for line in lines:
            if re.match(r'^(import|from|def|class)\s+', line) or (capture and (line.startswith('    ') or line.startswith('\t') or line.strip() == '')):
                capture = True
                buffer.append(line)
            else:
                if capture and line.strip() != "":
                    # Stop capturing if we hit non-indented text that isn't a keyword
                    pass
        
        if buffer:
            return "\n".join(buffer).strip()
            
        return text.strip()  # Fallback: return everything

    def sandbox_execute(self, code: str, timeout: int = 30) -> Tuple[Optional[int], str, str]:
        """Execute code in sandboxed subprocess with resource limits."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
            wrapped_code = f"""
import sys
import resource
import json
import math, collections, itertools, re

# Resource limits: 256MB RAM, 25s CPU
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_CPU, (25, 30))

try:
{re.sub(r'^', '    ', code, flags=re.MULTILINE)}
    _final_result = None
    _local_vars = locals()
    if 'answer' in _local_vars: _final_result = _local_vars['answer']
    elif 'result' in _local_vars: _final_result = _local_vars['result']
    else:
        for _v in reversed(list(_local_vars.values())):
            if isinstance(_v, (int, float)):
                _final_result = _v
                break
    print(f"RESULT_TOKEN:{{_final_result}}")
except MemoryError:
    print("EXEC_ERROR:MemoryError - sandbox limit exceeded", file=sys.stderr)
    sys.exit(137)
except Exception as e:
    print(f"EXEC_ERROR:{{e}}", file=sys.stderr)
"""
            tmp.write(wrapped_code)

        try:
            proc = subprocess.run(
                [sys.executable, '-u', tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            stdout, stderr = proc.stdout, proc.stderr
            match = re.search(r"RESULT_TOKEN:(.*)", stdout)
            prediction = None
            if match:
                val = match.group(1).strip()
                if val != "None":
                    try:
                        prediction = int(float(val))
                    except Exception:
                        pass
            return prediction, stdout, stderr
        except subprocess.TimeoutExpired:
            return None, "", f"TIMEOUT: Execution exceeded {timeout}s limit."
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _role_strateg(self, problem_text: str, strategy_type: str, rag_context: str) -> str:
        """Teza (Strateg) — Codestral: Generate initial solution."""
        strategy_instruction = self.strategies.get(strategy_type, self.strategies['symbolic'])
        
        prompt = f"""Ti si **Matematički Strateg**. Tvoj zadatak je da predložiš inicijalni matematički pristup i generišeš Python rešenje za problem. Koristi {strategy_type} pristup. {strategy_instruction}

Sav kod mora biti unutar `python` blokova. Fokusiraj se na simboličku preciznost (D1) i efikasnost resursa (D4). Izlaz mora sadržati samo kod bez suvišnog teksta.

RAG Context:
{rag_context}

Problem: {problem_text}

Generiši Python kod:"""
        
        messages = [{'role': 'user', 'content': prompt}]
        response, provider = self._query_api(messages)
        return response
    
    def _role_kriticar(self, problem_text: str, strateg_response: str) -> str:
        """Antiteza (Kritičar) — Mistral-Large: Identify errors and edge cases."""
        prompt = f"""Ti si **Matematički Kritičar**. Analiziraj predloženo rešenje i identifikuj sve potencijalne greške u logici, numeričkom opsegu (D2) ili nedefinisane delove sistema. Posebno proveri ekstremne slučajeve (D3) poput nula, beskonačnosti ili degenerisanih geometrijskih oblika. Tvoj cilj je da nađeš razlog zašto bi ovaj kod mogao pasti ili dati pogrešan rezultat.

Problem: {problem_text}

Predloženo rešenje (od Stratega):
{strateg_response}

Identifikuj greške i edge cases:"""
        
        messages = [{'role': 'user', 'content': prompt}]
        
        try:
            resp = self.mistral.chat.complete(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.3,
                timeout_ms=45000
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Kritičar (Mistral) failed: {e}")
            return "ERROR: Critic unavailable"
    
    def _role_nadzornik(self, problem_text: str, strateg_response: str, kriticar_response: str) -> str:
        """Sinteza (Nadzornik) — Gemini 2.0 Flash: Synthesize final solution."""
        prompt = f"""Ti si **Nadzornik (Overseer)**. Na osnovu debate između Stratega i Kritičara, sintetizuj finalni Python skript. Moraš osigurati da kod uključuje `try/except` blokove za samo-korekciju (D6) i da logika prati 'Chain-of-Thought' (D5). Finalni odgovor koji kod ispisuje mora biti isključivo nenegativan ceo broj kao **ostatak deljenja sa 100,000 (answer % 10^5)**. Ispis koda mora biti čist i spreman za izvršenje.

Problem: {problem_text}

Strateg (Teza):
{strateg_response}

Kritičar (Antiteza):
{kriticar_response}

Sintetizuj finalni Python kod:"""
        
        try:
            response = self.gemini.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ Nadzornik (Gemini) failed: {e}. Falling back to Strateg response.")
            return strateg_response
    
    def _trinity_debate(self, problem_text: str, strategy_type: str, rag_context: str) -> str:
        """Execute full Trinity 3-6-2 Dialectic (Teza → Antiteza → Sinteza)."""
        print(f"\n🔄 Trinity Debate — Strategy: {strategy_type}")
        
        # Step 1: Teza (Strateg)
        strateg_response = self._role_strateg(problem_text, strategy_type, rag_context)
        print(f"✅ Strateg completed")
        
        # Step 2: Antiteza (Kritičar)
        kriticar_response = self._role_kriticar(problem_text, strateg_response)
        print(f"✅ Kritičar completed")
        
        # Step 3: Sinteza (Nadzornik)
        nadzornik_response = self._role_nadzornik(problem_text, strateg_response, kriticar_response)
        print(f"✅ Nadzornik completed")
        
        return nadzornik_response
    
    def trinity_solve_with_voting(self, problem_id: int, problem_text: str, ground_truth: int):
        """5-Way Voting: Execute Trinity debate 5 times with different strategies, vote on final answer."""
        rag_results = self.rag.retrieve(problem_text, limit=2)
        rag_context = self.rag.format_for_prompt(rag_results)
        
        strategy_types = ['symbolic', 'brute-force', 'hybrid', 'alternative', 'creative']
        predictions = []
        
        for i, strategy in enumerate(strategy_types, 1):
            print(f"\n{'='*60}")
            print(f"🎯 Run {i}/5 — Strategy: {strategy.upper()}")
            print(f"{'='*60}")
            
            # Execute Trinity Debate
            final_response = self._trinity_debate(problem_text, strategy, rag_context)
            
            # Extract and validate code
            code = self.extract_code(final_response)
            
            if not code:
                print(f"❌ No code extracted for strategy: {strategy}")
                predictions.append(None)
                continue
            
            syntax_ok, security_veto = SolverValidator.validate(code)
            
            if not syntax_ok:
                print(f"❌ Security/Syntax veto for {strategy}: {security_veto}")
                predictions.append(None)
                continue
            
            # Execute code
            prediction, stdout, stderr = self.sandbox_execute(code)
            predictions.append(prediction)
            
            print(f"📊 Prediction: {prediction}")
            
            # Save individual run to DB
            self._save(
                problem_id=problem_id,
                problem_text=problem_text,
                raw_response=final_response,
                code=code,
                prediction=prediction,
                ground_truth=ground_truth,
                success=(prediction == ground_truth) if prediction is not None else False,
                syntax_ok=1 if syntax_ok else 0,
                security_veto=security_veto if not syntax_ok else "",
                provider=f"trinity_{strategy}",
                stdout=stdout,
                stderr=stderr,
                error_log="" if prediction is not None else stderr,
                attempt=i
            )
        
        # Majority Voting
        valid_predictions = [p for p in predictions if p is not None]
        
        if not valid_predictions:
            print("\n❌ No valid predictions from any strategy.")
            return False
        
        vote_counts = Counter(valid_predictions)
        final_prediction = vote_counts.most_common(1)[0][0]
        
        print(f"\n{'='*60}")
        print(f"🗳️  VOTING RESULTS")
        print(f"{'='*60}")
        print(f"Predictions: {predictions}")
        print(f"Vote Counts: {dict(vote_counts)}")
        print(f"Final Prediction (Majority): {final_prediction}")
        print(f"Ground Truth: {ground_truth}")
        print(f"Success: {final_prediction == ground_truth}")
        print(f"{'='*60}\n")
        
        return final_prediction == ground_truth
    
    def solve(self, problem_id: int, problem_text: str, ground_truth: int):
        rag_results = self.rag.retrieve(problem_text, limit=2)
        rag_context = self.rag.format_for_prompt(rag_results)
        
        # CORRECTED: Include system prompt in the messages list
        messages = [
            {'role': 'system', 'content': f"You are a master AIMO solver. Return ONLY Python code in ```python blocks.\n{rag_context}"},
            {'role': 'user', 'content': f"Problem: {problem_text}"}
        ]
        
        # Retry Loop (Max 3 attempts for Extraction/Syntax)
        success = False
        
        for attempt in range(1, 4):
            # Append context for retry
            if attempt > 1:
                messages.append({'role': 'user', 'content': f"Attempt {attempt}/3: Previous code extraction failed or had syntax errors. Please provide valid Python code in ```python``` blocks."})
            
            raw_response, provider = self._query_api(messages)
            code = self.extract_code(raw_response)
            
            if not code:
                syntax_ok_bool, security_veto = False, "No code found"
            else:
                syntax_ok_bool, security_veto = SolverValidator.validate(code)
                
            syntax_ok = 1 if syntax_ok_bool else 0
            
            if syntax_ok_bool:
                # Valid code found, execute it
                prediction, stdout, stderr = self.sandbox_execute(code)
                success = (prediction == ground_truth) if prediction is not None else False
                
                self._save(
                    problem_id=problem_id, problem_text=problem_text, raw_response=raw_response,
                    code=code, prediction=prediction, ground_truth=ground_truth,
                    success=success, syntax_ok=syntax_ok, security_veto=security_veto,
                    provider=provider, stdout=stdout, stderr=stderr, 
                    error_log=stderr if not success else "", attempt=attempt
                )
                break # Exit loop if syntax valid (even if prediction wrong)
            else:
                # Syntax/Security Error - Retry
                self._save(
                    problem_id=problem_id, problem_text=problem_text, raw_response=raw_response,
                    code=code, prediction=None, ground_truth=ground_truth,
                    success=False, syntax_ok=syntax_ok, security_veto=security_veto,
                    provider=provider, stdout="", stderr="", 
                    error_log="Syntax/Extraction Failed", attempt=attempt
                )
                messages.append({'role': 'assistant', 'content': raw_response})
                pass

        return success

    def _save(self, **kwargs):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO aimo_history 
            (problem_id, problem_text, raw_response, code, prediction, ground_truth, success, syntax_ok, security_veto, provider, stdout, stderr, error_log, timestamp, attempt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kwargs.get('problem_id'), kwargs.get('problem_text'), kwargs.get('raw_response'),
            kwargs.get('code'), kwargs.get('prediction'), kwargs.get('ground_truth'),
            kwargs.get('success'), kwargs.get('syntax_ok'), kwargs.get('security_veto'),
            kwargs.get('provider'), kwargs.get('stdout'), kwargs.get('stderr'),
            kwargs.get('error_log'), datetime.now().isoformat(), kwargs.get('attempt', 1)
        ))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    solver = TrinitySolver()
    
    # Trinity 5-Way Voting Example
    print("🚀 AIMO Trinity Solver — 5-Way Voting System")
    print("="*60)
    
    # Test problem: Find 5! (factorial of 5)
    success = solver.trinity_solve_with_voting(
        problem_id=99,
        problem_text="Calculate the factorial of 5 and return the result modulo 100000.",
        ground_truth=120
    )
    
    print(f"\n{'='*60}")
    print(f"Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"{'='*60}")
