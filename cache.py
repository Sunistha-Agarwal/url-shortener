import redis
from database import SessionLocal
from models import URL
from config import REDIS_HOST, REDIS_PORT


client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_cached_url(short_code: str) -> str|None:
    return client.get(short_code)

def cache_url(short_code: str, url: str):
    client.set(short_code, url, ex=604800) #7 days ttl

def invalidate_url(short_code: str):
    client.delete(short_code)

def increment_click_cache(short_code: str):
    client.incr(f"clicks:{short_code}")

def get_cached_clicks(short_code: str)-> int:
    val = client.get(f"clicks:{short_code}")
    return int(val) if val else 0

def flush_clicks_to_db():
    db = SessionLocal()
    try:
        url_keys = client.keys("clicks:*")
        for key in url_keys:
            short_code = key.split(":")[1]
            clicks = client.getdel(key)
            if not clicks:
                continue
            db.query(URL).filter(URL.short_code == short_code).update({"clicks": clicks+URL.clicks})
        db.commit()
    finally:
        db.close()