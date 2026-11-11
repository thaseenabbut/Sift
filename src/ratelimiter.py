import math
import redis.asyncio as redis

from rich import print


class RedisRateLimiter:
    
    TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local interval = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local should_consume = tonumber(ARGV[5]) == 1
local ttl = tonumber(ARGV[6])

local now = redis.call('TIME')
local now_seconds = tonumber(now[1]) + tonumber(now[2]) / 1000000

local stored = redis.call('HMGET', key, 'tokens', 'last_refill_at')
local tokens = tonumber(stored[1])
local last_refill_at = tonumber(stored[2])

if tokens == nil or last_refill_at == nil then
  tokens = max_tokens
  last_refill_at = now_seconds
end

local elapsed = now_seconds - last_refill_at
if elapsed > 0 then
  local refill_amount = math.floor(elapsed * refill_rate / interval)
  if refill_amount > 0 then
    tokens = math.min(max_tokens, tokens + refill_amount)
    last_refill_at = last_refill_at + refill_amount * interval / refill_rate
  end
end

local allowed = 0
if tokens >= requested then
  allowed = 1
  if should_consume then
    tokens = tokens - requested
  end
end

if should_consume then
  redis.call(
    'HSET', key,
    'tokens', tostring(tokens),
    'last_refill_at', tostring(last_refill_at)
  )
  redis.call('EXPIRE', key, ttl)
end

local retry_after = 0
if allowed == 0 then
  retry_after = math.ceil((requested - tokens) * interval / refill_rate)
end

return {allowed, math.floor(tokens), retry_after}
"""

    def __init__(
        self,
        redis_client: redis.Redis,
        max_tokens: int,
        refill_rate: float,
        interval: float,
        key_prefix: str = "sift:ratelimit:",
        key_ttl: int | None = None,
    ):
        
        assert max_tokens > 0, "max_tokens must be positive"
        assert refill_rate > 0, "refill_rate must be positive"
        assert interval > 0, "interval must be positive"
                
        self.redis_client = redis_client
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.interval = interval
        self.key_prefix = key_prefix
        self.key_ttl = (
            key_ttl
            if key_ttl is not None
            else max(1, math.ceil(max_tokens * interval / refill_rate))
        )
        
        try:
            self._script = redis_client.register_script(self.TOKEN_BUCKET_LUA)
        except Exception as e:
            print(f"[bold yellow][WARNING][/bold yellow] Failed to register Lua script with Redis: {e}")
            self._script = None

    def _key(self, client_ip: str) -> str:
        return f"{self.key_prefix}{client_ip}"

    async def _evaluate(self, client_ip: str, tokens: int, consume: bool) -> tuple[bool, int, float]:
        if self._script is None:
            return False, 0, 0

        try:
          allowed, remaining, retry_after = await self._script(
              keys=[self._key(client_ip)],
              args=[
                  self.max_tokens,
                  self.refill_rate,
                  self.interval,
                  tokens,
                  1 if consume else 0,
                  self.key_ttl,
              ],
          )
          return bool(allowed), int(remaining), float(retry_after)
        except Exception as e:
            print(f"[bold yellow][WARNING][/bold yellow] Failed to evaluate Lua script with Redis: {e}")
            raise

    async def check(self, client_ip: str, tokens: int = 1) -> tuple[bool, int, float]:
        return await self._evaluate(client_ip, tokens, consume=False)
        

    async def consume(self, client_ip: str, tokens: int = 1) -> bool:
        
        if tokens <= 0:
            raise ValueError("tokens must be positive")
                    
        if tokens > self.max_tokens:
            raise ValueError("tokens cannot exceed max_tokens")
                    
        allowed, _, _ = await self._evaluate(client_ip, tokens, consume=True)
        return allowed

    async def retry_after(self, client_ip: str, tokens: int = 1) -> float:
        _, _, retry_after = await self.check(client_ip, tokens)
        return retry_after
