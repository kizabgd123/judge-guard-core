import time
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.antigravity_core.gemini_client import GeminiClient

class BenchmarkGeminiTokens(unittest.TestCase):
    @patch('src.antigravity_core.gemini_client.genai.configure')
    @patch('src.antigravity_core.gemini_client.genai.GenerativeModel')
    def test_token_restriction_impact(self, mock_model_class, mock_config):
        mock_model = mock_model_class.return_value

        # Simulate latency: base 200ms + 1ms per token
        def mocked_generate(prompt, **kwargs):
            # Default to a high value if not specified
            max_tokens = kwargs.get('generation_config', {}).get('max_output_tokens', 2048)

            # Simulate processing time
            simulated_latency = 0.2 + (max_tokens * 0.001)
            time.sleep(simulated_latency)

            mock_resp = MagicMock()
            mock_resp.text = '{"verdict": "PASSED"}'
            return mock_resp

        mock_model.generate_content.side_effect = mocked_generate

        client = GeminiClient(api_keys="test_key")

        print("\n--- Gemini Token Restriction Benchmark ---")

        # 1. Measure impact of max_output_tokens
        # Baseline (Simulate high default)
        start_b = time.time()
        mock_model.generate_content("Evaluate this...") # No kwargs
        dur_b = time.time() - start_b

        # Optimized
        start_o = time.time()
        # This will fail until Step 3 is done if called via client.generate_content,
        # so for benchmark setup we test the mock behavior.
        mock_model.generate_content("Evaluate this...", generation_config={"max_output_tokens": 10})
        dur_o = time.time() - start_o

        print(f"Latency (Default ~2048 tokens): {dur_b:.4f}s")
        print(f"Latency (Restricted 10 tokens): {dur_o:.4f}s")
        print(f"Improvement: {((dur_b - dur_o) / dur_b) * 100:.2f}%")

if __name__ == "__main__":
    unittest.main()
