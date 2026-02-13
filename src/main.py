"""
Tiny Link - Self-hosted URL shortener with click tracking
"""
import os
import json
import secrets
import string
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv

load_dotenv()

# Config
DATA_DIR = Path(os.getenv("TINYLINK_DATA_DIR", "/root/source/side-projects/tiny-link/data"))
BASE_URL = os.getenv("TINYLINK_BASE_URL", "http://localhost:8083")
DEFAULT_CODE_LENGTH = 6

# In-memory store (backed by JSON file)
links: dict[str, dict] = {}


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "clicks").mkdir(exist_ok=True)


def load_links():
    global links
    links_file = DATA_DIR / "links.json"
    if links_file.exists():
        links = json.loads(links_file.read_text())


def save_links():
    ensure_dirs()
    links_file = DATA_DIR / "links.json"
    links_file.write_text(json.dumps(links, indent=2))


def generate_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a random short code."""
    alphabet = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if code not in links:
            return code


def log_click(code: str, request: Request):
    """Log a click event."""
    ensure_dirs()
    log_file = DATA_DIR / "clicks" / f"{date.today().isoformat()}.jsonl"
    
    record = {
        "code": code,
        "time": datetime.utcnow().isoformat(),
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", "")[:200],
        "referer": request.headers.get("referer", ""),
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def get_click_stats(code: str) -> dict:
    """Get click statistics for a link."""
    clicks_dir = DATA_DIR / "clicks"
    if not clicks_dir.exists():
        return {"total": 0, "recent": []}
    
    total = 0
    recent = []
    
    for log_file in sorted(clicks_dir.glob("*.jsonl"), reverse=True):
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    click = json.loads(line)
                    if click["code"] == code:
                        total += 1
                        if len(recent) < 10:
                            recent.append(click)
    
    return {"total": total, "recent": recent}


# FastAPI app
app = FastAPI(
    title="Tiny Link",
    description="Self-hosted URL shortener",
    version="0.1.0",
)


@app.on_event("startup")
async def startup():
    ensure_dirs()
    load_links()
    print(f"🔗 Tiny Link started with {len(links)} links")


class LinkCreate(BaseModel):
    url: HttpUrl
    code: str | None = None  # Custom code (optional)
    expires_at: str | None = None  # ISO datetime (optional)


class LinkResponse(BaseModel):
    code: str
    short_url: str
    original_url: str
    created_at: str
    clicks: int


@app.get("/")
async def root():
    return {
        "name": "Tiny Link",
        "total_links": len(links),
        "base_url": BASE_URL,
        "api": {
            "create": "POST /api/links",
            "list": "GET /api/links",
            "stats": "GET /api/links/{code}/stats",
            "delete": "DELETE /api/links/{code}",
        }
    }


@app.post("/api/links", response_model=LinkResponse)
async def create_link(data: LinkCreate):
    """Create a new short link."""
    url = str(data.url)
    
    # Validate URL
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL scheme")
    
    # Use custom code or generate one
    if data.code:
        if data.code in links:
            raise HTTPException(status_code=409, detail="Code already exists")
        if not data.code.isalnum():
            raise HTTPException(status_code=400, detail="Code must be alphanumeric")
        code = data.code
    else:
        code = generate_code()
    
    # Create link record
    links[code] = {
        "url": url,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": data.expires_at,
        "clicks": 0,
    }
    save_links()
    
    return LinkResponse(
        code=code,
        short_url=f"{BASE_URL}/{code}",
        original_url=url,
        created_at=links[code]["created_at"],
        clicks=0,
    )


@app.get("/api/links")
async def list_links(limit: int = 50):
    """List all short links."""
    result = []
    for code, data in list(links.items())[:limit]:
        result.append({
            "code": code,
            "short_url": f"{BASE_URL}/{code}",
            "original_url": data["url"],
            "created_at": data["created_at"],
            "clicks": data.get("clicks", 0),
        })
    
    return {"links": result, "total": len(links)}


@app.get("/api/links/{code}")
async def get_link(code: str):
    """Get link details."""
    if code not in links:
        raise HTTPException(status_code=404, detail="Link not found")
    
    data = links[code]
    return {
        "code": code,
        "short_url": f"{BASE_URL}/{code}",
        "original_url": data["url"],
        "created_at": data["created_at"],
        "clicks": data.get("clicks", 0),
    }


@app.get("/api/links/{code}/stats")
async def get_link_stats(code: str):
    """Get detailed click statistics for a link."""
    if code not in links:
        raise HTTPException(status_code=404, detail="Link not found")
    
    data = links[code]
    stats = get_click_stats(code)
    
    return {
        "code": code,
        "original_url": data["url"],
        "created_at": data["created_at"],
        "total_clicks": stats["total"],
        "recent_clicks": stats["recent"],
    }


@app.delete("/api/links/{code}")
async def delete_link(code: str):
    """Delete a short link."""
    if code not in links:
        raise HTTPException(status_code=404, detail="Link not found")
    
    del links[code]
    save_links()
    
    return {"ok": True, "deleted": code}


# Redirect endpoint (the main purpose!)
@app.get("/{code}")
async def redirect(code: str, request: Request):
    """Redirect short URL to original."""
    if code not in links:
        raise HTTPException(status_code=404, detail="Link not found")
    
    data = links[code]
    
    # Check expiration
    if data.get("expires_at"):
        if datetime.fromisoformat(data["expires_at"]) < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Link expired")
    
    # Update click count
    data["clicks"] = data.get("clicks", 0) + 1
    save_links()
    
    # Log click
    log_click(code, request)
    
    return RedirectResponse(url=data["url"], status_code=302)


@app.get("/health")
async def health():
    return {"status": "ok", "links": len(links)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
