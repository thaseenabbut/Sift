import hashlib
import json
from rich import print

def generate_cache_key(query, bm25_parameters, index_version):
    query_hash = hashlib.sha256(
        query.encode("utf-8")
    ).hexdigest()

    k1 = bm25_parameters["k1"]
    b = bm25_parameters["b"]

    return f"sift:search:v{index_version}:{query_hash}:k1={k1}:b={b}"

async def get_cached_results(redis_manager, cache_key):
    if redis_manager.redis_client is None:
        return None
    try:
        cached_results = await redis_manager.redis_client.get(cache_key)

        if cached_results is not None:
            return json.loads(cached_results)
        else:
            return None

    except Exception as e:
        print(f"[bold red][ERROR][/bold red] Could not retrieve cache from Redis. {type(e).__name__}: {e}")
        return None
    
async def set_cached_results(redis_manager, cache_key, results, expiration=300):
    if redis_manager.redis_client is None:
        return None
    try:
        await redis_manager.redis_client.setex(
            cache_key, expiration, json.dumps(results)
        )
        print(f"[bold green][CACHE SET][/bold green] Cache set for key: {cache_key} with expiration: {expiration} seconds.")
    except Exception as e:
        print(f"[bold red][ERROR][/bold red] Could not set cache: {type(e).__name__}: {e}")
        return None
