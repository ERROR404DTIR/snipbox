import tempfile
import unittest
from pathlib import Path

from snipbox.store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "s.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_get(self):
        s = self.store.add("Hello", "print('hi')", ["Python", " py "])
        self.assertEqual(s["id"], 1)
        self.assertEqual(s["tags"], ["py", "python"])
        self.assertEqual(self.store.get(1)["content"], "print('hi')")

    def test_ids_never_reused(self):
        self.store.add("a", "x")
        self.store.remove(1)
        self.assertEqual(self.store.add("b", "y")["id"], 2)

    def test_search_all_words(self):
        self.store.add("git undo", "git reset --soft HEAD~1", ["git"])
        self.store.add("docker", "docker ps -a", ["docker"])
        self.assertEqual(len(self.store.search("git reset")), 1)
        self.assertEqual(len(self.store.search("nothing")), 0)

    def test_filter_by_tag_and_tags_count(self):
        self.store.add("a", "x", ["one", "two"])
        self.store.add("b", "y", ["two"])
        self.assertEqual(len(self.store.list("two")), 2)
        self.assertEqual(self.store.tags(), {"one": 1, "two": 2})

    def test_remove_missing(self):
        self.assertFalse(self.store.remove(42))

    def test_unicode(self):
        self.store.add("سلام", "متن فارسی", ["فارسی"])
        self.assertEqual(len(self.store.search("فارسی")), 1)


if __name__ == "__main__":
    unittest.main()
