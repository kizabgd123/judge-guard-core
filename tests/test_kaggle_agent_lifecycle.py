import unittest
from src.kaggle_stream.kaggle_agent import KaggleAgent
import os

class TestKaggleAgentLifecycle(unittest.TestCase):
    def test_executor_shutdown_on_close(self):
        agent = KaggleAgent(name="LifecycleTest")
        # ⚡ Bolt: Access the property to trigger lazy initialization
        executor = agent.executor
        self.assertFalse(executor._shutdown)
        agent.close()
        self.assertTrue(executor._shutdown)

    def test_context_manager_shutdown(self):
        with KaggleAgent(name="ContextTest") as agent:
            # ⚡ Bolt: Access the property to trigger lazy initialization
            executor = agent.executor
            self.assertFalse(executor._shutdown)
        self.assertTrue(executor._shutdown)

if __name__ == "__main__":
    unittest.main()
