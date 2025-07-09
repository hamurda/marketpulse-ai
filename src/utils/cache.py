import os
import json
import hashlib
import time
from typing import Any

CACHE_DIR = "data/cache"
CACHE_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours

os.makedirs(CACHE_DIR, exist_ok=True)

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def _get_cache_file_path(key: str) -> str:
    return os.path.join(CACHE_DIR, _hash_key(key) + ".json")

def save_to_cache(key: str, data: Any):
    filepath = _get_cache_file_path(key)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_from_cache(key: str):
    filepath = _get_cache_file_path(key)
    if not os.path.exists(filepath):
        return None

    # Check expiration
    modified_time = os.path.getmtime(filepath)
    current_time = time.time()
    age = current_time - modified_time

    if age > CACHE_EXPIRATION_SECONDS:
        print(f"[CACHE] Cache expired for key: {key}")
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"[CACHE] Failed to remove expired cache file: {e}")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        print("[CACHE] Using valid cache")
        return json.load(f)
