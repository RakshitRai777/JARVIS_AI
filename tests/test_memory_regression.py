import os
import unittest
import memory_manager
from hybrid_memory import hybrid_memory_search


class TestMemoryRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        memory_manager.MEMORY_FILE = "test_memory_regression.json"
        if os.path.exists(memory_manager.MEMORY_FILE):
            os.remove(memory_manager.MEMORY_FILE)
        memory_manager.load()

        # Seed large memory
        for i in range(50):
            memory_manager.add_memory(
                f"Fact number {i} is important",
                tags=["fact"]
            )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(memory_manager.MEMORY_FILE):
            os.remove(memory_manager.MEMORY_FILE)

    def test_old_memory_retrievable(self):
        results = hybrid_memory_search("Fact number 3", limit=3)
        self.assertTrue(any("Fact number 3" in r["text"] for r in results))

    def test_new_memory_retrievable(self):
        memory_manager.add_memory("Latest critical fact", tags=["fact"])
        results = hybrid_memory_search("critical", limit=3)
        self.assertTrue(any("Latest critical fact" in r["text"] for r in results))

    def test_no_duplicates(self):
        results = hybrid_memory_search("fact", limit=10)
        texts = [r["text"] for r in results]
        self.assertEqual(len(texts), len(set(texts)))
