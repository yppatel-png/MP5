"""
Hash-keyed caching layer for LLM responses.
Ensures idempotent execution, zero redundant API token expenditure, and instant replays.
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional

class LLMCache:
    def __init__(self):
        # In-memory storage: hash_key -> {response, timestamp, hits}
        self._cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def compute_key(model: str, messages: Any, temperature: float = 0.0, **kwargs) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "kwargs": {k: v for k, v in sorted(kwargs.items()) if k not in ["api_key", "base_url"]}
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(key)
        if entry:
            entry["hits"] += 1
            return entry["data"]
        return None

    def set(self, key: str, data: Dict[str, Any]) -> None:
        self._cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "hits": 0
        }

    def clear(self) -> None:
        self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        total_hits = sum(e["hits"] for e in self._cache.values())
        return {
            "cached_entries": len(self._cache),
            "cache_hits": total_hits
        }

llm_cache = LLMCache()

