import os
from dotenv import load_dotenv

import redis.asyncio as redis

from redis.exceptions import RedisError
from rich import print

_ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(_ENV_PATH)

class RedisManager:
    def __init__(self):
        self.redis_client = None
        
    async def connect_redis(self):
        print("[bold green][CONNECTING REDIS][/bold green] Connecting to Redis...")
        
        try:
            self.redis_client = redis.Redis(
                host= os.getenv('REDIS_HOST'),
                port= int(os.getenv('REDIS_PORT')),
                password= os.getenv('REDIS_PASSWORD'),
                db= int(os.getenv('REDIS_DB')),
            )
            
            await self.redis_client.ping()
            print("[bold green][CONNECTED REDIS][/bold green] Redis connected")
        
        except RedisError as e:
            print("[bold red][CONNECTION REDIS FAILED][/bold red] Redis connection failed: ", e)
            self.redis_client = None
            return None
        
        return self.redis_client
        
    async def close_redis(self):
        try:
            if self.redis_client:
                await self.redis_client.aclose()
                self.redis_client = None
                print("[bold red][DISCONNECTED REDIS][/bold red] Redis connection closed")
        except Exception as e:
            print("[bold red][CONNECTION REDISCLOSE FAILED][/bold red] Redis connection close failed: ", e)

redis_manager = RedisManager()