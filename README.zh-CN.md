[English](README.md) | [中文](README.zh-CN.md)

# 🔗 Tiny Link

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

自托管短链接服务，支持点击统计。

## 功能

- 🎯 自定义短码或自动生成
- 📊 点击统计和访客信息
- ⏰ 可选链接过期时间
- 💾 JSON 文件存储，零依赖

## 快速开始

```bash
cd /root/source/side-projects/tiny-link

# 安装依赖
pip install fastapi uvicorn python-dotenv

# 配置
cp .env.example .env
# 编辑 .env，设置 TINYLINK_BASE_URL 为你的域名

# 运行
uvicorn src.main:app --port 8083
```

## 使用

### 创建短链接

```bash
# 自动生成短码
curl -X POST http://localhost:8083/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url"}'

# 自定义短码
curl -X POST http://localhost:8083/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "code": "mylink"}'
```

### 跳转

```
http://localhost:8083/abc123 → https://example.com/very/long/url
```

### 查看统计

```bash
curl http://localhost:8083/api/links/abc123/stats
```

## API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/{code}` | GET | 跳转到原始 URL |
| `/api/links` | GET | 列出所有链接 |
| `/api/links` | POST | 创建新链接 |
| `/api/links/{code}` | GET | 获取链接详情 |
| `/api/links/{code}/stats` | GET | 点击统计 |
| `/api/links/{code}` | DELETE | 删除链接 |

### 在线体验

```bash
# 创建短链接
curl -X POST https://s.indiekit.ai/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/indiekitai"}'

# 查看统计
curl https://s.indiekit.ai/api/links/{code}/stats
```

## 数据存储

```
data/
├── links.json         # 所有短链接
└── clicks/
    └── 2026-02-13.jsonl  # 每日点击日志
```

## License

MIT
