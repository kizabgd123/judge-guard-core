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

# ============ TRINITY SOLVER ============
class TrinitySolver:
    def __init__(self):
        self.db_path = 'trinity_aimo.db'
        self.mistral = Mistral(api_key=os.getenv('MISTRAL_API_KEY', ''))
        self.rag = TrinityRAG()
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
                    return resp.json()['choices'][0]['message']['content'], "openrouter/deepseek"
                print(f"❌ OpenRouter error: {resp.status_code} - {resp.text}")
                return "", "FAILED"
            except Exception as or_e:
                print(f"❌ Failover failed: {or_e}")
                return "", "FAILED"

    def extract_code(self, text: str) -> str:
        if not text: return ""
        code_match = re.search(r'```python\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
        if code_match:
            return code_match.group(1).strip()
        code_match = re.search(r'```(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return text.strip()

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

    def solve(self, problem_id: int, problem_text: str, ground_truth: int):
        rag_results = self.rag.retrieve(problem_text, limit=2)
        rag_context = self.rag.format_for_prompt(rag_results)
        
        # CORRECTED: Include system prompt in the messages list
        messages = [
            {'role': 'system', 'content': f"You are a master AIMO solver. Return ONLY Python code in ```python blocks.\n{rag_context}"},
            {'role': 'user', 'content': f"Problem: {problem_text}"}
        ]
        
        raw_response, provider = self._query_api(messages)
        code = self.extract_code(raw_response)
        
        if not code:
            syntax_ok_bool, security_veto = False, "No code found"
        else:
            syntax_ok_bool, security_veto = SolverValidator.validate(code)
            
        syntax_ok = 1 if syntax_ok_bool else 0
        prediction, stdout, stderr = (None, "", security_veto) if not syntax_ok_bool else self.sandbox_execute(code)
        
        success = (prediction == ground_truth) if prediction is not None else False
        
        self._save(
            problem_id=problem_id, problem_text=problem_text, raw_response=raw_response,
            code=code, prediction=prediction, ground_truth=ground_truth,
            success=success, syntax_ok=syntax_ok, security_veto=security_veto,
            provider=provider, stdout=stdout, stderr=stderr, error_log=stderr if not success else ""
        )
        return success

    def _save(self, **kwargs):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO aimo_history 
            (problem_id, problem_text, raw_response, code, prediction, ground_truth, success, syntax_ok, security_veto, provider, stdout, stderr, error_log, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kwargs.get('problem_id'), kwargs.get('problem_text'), kwargs.get('raw_response'),
            kwargs.get('code'), kwargs.get('prediction'), kwargs.get('ground_truth'),
            kwargs.get('success'), kwargs.get('syntax_ok'), kwargs.get('security_veto'),
            kwargs.get('provider'), kwargs.get('stdout'), kwargs.get('stderr'),
            kwargs.get('error_log'), datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    solver = TrinitySolver()
    solver.solve(99, "Find 5!", 120)
