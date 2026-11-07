"""JSON-backed storage for snippets."""
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional


def default_path() -> Path:
    env = os.environ.get("SNIPBOX_FILE")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".snipbox" / "snippets.json"


class Store:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else default_path()

    # ---- persistence -------------------------------------------------
    def _load(self) -> Dict:
        if not self.path.exists():
            return {"next_id": 1, "snippets": []}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # atomic write: never leave a half-written file behind
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # ---- operations --------------------------------------------------
    def add(self, title: str, content: str, tags: Optional[List[str]] = None) -> Dict:
        data = self._load()
        snippet = {
            "id": data["next_id"],
            "title": title.strip(),
            "content": content,
            "tags": sorted({t.strip().lower() for t in (tags or []) if t.strip()}),
            "created": int(time.time()),
        }
        data["next_id"] += 1
        data["snippets"].append(snippet)
        self._save(data)
        return snippet

    def get(self, snippet_id: int) -> Optional[Dict]:
        for s in self._load()["snippets"]:
            if s["id"] == snippet_id:
                return s
        return None

    def list(self, tag: Optional[str] = None) -> List[Dict]:
        items = self._load()["snippets"]
        if tag:
            tag = tag.lower()
            items = [s for s in items if tag in s["tags"]]
        return items

    def search(self, query: str) -> List[Dict]:
        words = query.lower().split()
        results = []
        for s in self._load()["snippets"]:
            haystack = " ".join([s["title"], s["content"], " ".join(s["tags"])]).lower()
            if all(w in haystack for w in words):
                results.append(s)
        return results

    def remove(self, snippet_id: int) -> bool:
        data = self._load()
        before = len(data["snippets"])
        data["snippets"] = [s for s in data["snippets"] if s["id"] != snippet_id]
        if len(data["snippets"]) == before:
            return False
        self._save(data)
        return True

    def tags(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in self._load()["snippets"]:
            for t in s["tags"]:
                counts[t] = counts.get(t, 0) + 1
        return dict(sorted(counts.items()))
