import time
from redis.asyncio import from_url
from fastapi import HTTPException, Request
from app.core.config import settings

redis = from_url(settings.redis_url, decode_responses=True)


async def enforce(request: Request):
    ip = request.client.host if request.client else "unknown"
    bucket = f"rl:{ip}:{int(time.time() // 60)}"
    count = await redis.incr(bucket)
    if count == 1:
        await redis.expire(bucket, 65)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
