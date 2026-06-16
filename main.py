from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from models import ShortenRequest, URL
from database import create_tables, get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from cache import get_cached_url, cache_url, invalidate_url, increment_click_cache, get_cached_clicks, flush_clicks_to_db
from apscheduler.schedulers.background import BackgroundScheduler
import hashlib
from config import BASE_URL
from routers import auth
from auth import get_current_user
from pathlib import Path

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

create_tables()

app.include_router(auth.router)

scheduler = BackgroundScheduler()
scheduler.add_job(flush_clicks_to_db, 'interval', hours=1)
scheduler.start()

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return Path("static/index.html").read_text(encoding='utf-8')

@app.post('/shorten')
def shorten_code(request: ShortenRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    url = str(request.url)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    short_code = url_hash[:8]
    
    existing = db.query(URL).filter(URL.short_code == short_code).first()
    if existing:
        return {"short_code": existing.short_code, "short_url":f"{BASE_URL}/{existing.short_code}"}

    new_url = URL(short_code=short_code, url=url, owner_id=current_user.id)
    db.add(new_url)
    db.commit()
    return {"short_code": short_code, "short_url":f"{BASE_URL}/{short_code}"}

@app.get('/my-urls')
def get_my_urls(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    urls = db.query(URL).filter(URL.owner_id == current_user.id).all()
    return [{"short_code": u.short_code, "url": u.url, "clicks": u.clicks} for u in urls]
@app.get('/stats/{short_code}')
def get_stats(short_code: str, db: Session = Depends(get_db)):
    result = db.query(URL).filter(URL.short_code == short_code).first()
    cached_clicks = get_cached_clicks(short_code)
    if result:
        total_clicks = result.clicks + cached_clicks
        return{
            "short_code": result.short_code,
            "url": result.url,
            "clicks": total_clicks,
            "created_at": result.created_at
        }
    else:
        raise HTTPException(status_code=404, detail="URL not found")

@app.get('/{short_code}')
def redirect_user(short_code: str,  db: Session = Depends(get_db)):

    if len(short_code) != 8:
        raise HTTPException(status_code=400, detail="Invalid short code")

    cache_result = get_cached_url(short_code)
    if cache_result: 
        increment_click_cache(short_code)
        return RedirectResponse(cache_result)
    result = db.query(URL).filter(URL.short_code == short_code).first()
    if result:
        age = datetime.now() - result.created_at
        if age > timedelta(days=7):
            invalidate_url(short_code)
            raise HTTPException(status_code=410, detail="URL has expired")
        cache_url(short_code, result.url)
        increment_click_cache(short_code)
        db.commit()
        return RedirectResponse(result.url)
    else:
        raise HTTPException(status_code=404, detail="URL not found")

 
