# 🔗 Tiny Link

Self-hosted URL shortener with click tracking.

自托管短链接服务，支持点击统计。

## Features

- 🎯 自定义短码或自动生成
- 📊 点击统计和访客信息
- ⏰ 可选链接过期时间
- 💾 JSON 文件存储，零依赖

## Quick Start

```bash
cd /root/source/side-projects/tiny-link

# Install
pip install fastapi uvicorn python-dotenv

# Configure
cp .env.example .env
# Edit: set TINYLINK_BASE_URL to your domain

# Run
uvicorn src.main:app --port 8083
```

## Usage

### Create Short Link

```bash
# Auto-generate code
curl -X POST http://localhost:8083/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url"}'

# Custom code
curl -X POST http://localhost:8083/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "code": "mylink"}'
```

### Redirect

```
http://localhost:8083/abc123 → https://example.com/very/long/url
```

### View Stats

```bash
curl http://localhost:8083/api/links/abc123/stats
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{code}` | GET | Redirect to original URL |
| `/api/links` | GET | List all links |
| `/api/links` | POST | Create new link |
| `/api/links/{code}` | GET | Get link details |
| `/api/links/{code}/stats` | GET | Click statistics |
| `/api/links/{code}` | DELETE | Delete link |

## Data Storage

```
data/
├── links.json         # All short links
└── clicks/
    └── 2026-02-13.jsonl  # Daily click logs
```

## License

MIT
