# Headless Browser MCP Server

A local MCP server that fetches web pages using a real headless browser (Playwright), bypassing bot detection that blocks simple HTTP requests.

## Why?

Many sites (Medium, Substack, paywalled content) block programmatic access but allow real browsers. This server:
- Uses Playwright to load pages in a real Chromium browser
- Extracts clean article content using trafilatura
- Returns markdown-formatted text with metadata
- Exposes this as an MCP tool for Claude Code

## Setup

### 1. Create virtual environment

```bash
cd /path/to/clerk/tools/headless-browser
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers

```bash
playwright install chromium
```

### 4. Configure Claude Code

Add to `~/.claude.json` in the `mcpServers` section:

```json
{
  "mcpServers": {
    "headless-browser": {
      "command": "/path/to/clerk/tools/headless-browser/venv/bin/python",
      "args": ["/path/to/clerk/tools/headless-browser/server.py"]
    }
  }
}
```

Replace `/path/to/clerk` with your actual clerk installation path (e.g., `${HOME}/clerk`).

### 5. Restart Claude Code

The `fetch_url` and `fetch_urls` tools should now be available.

## Tools

### fetch_url

Fetch a single URL and extract its content.

**Parameters:**
- `url` (required): The URL to fetch
- `wait_seconds` (optional, default 2.0): Time to wait for dynamic content

**Returns:** Markdown-formatted article with title, author, date, and content.

### fetch_urls

Fetch multiple URLs in parallel.

**Parameters:**
- `urls` (required): Array of URLs to fetch
- `wait_seconds` (optional, default 2.0): Time to wait for dynamic content

**Returns:** Combined results for all URLs.

## Testing

Test the server directly:

```bash
source venv/bin/activate
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python server.py
```

Or test a URL fetch:

```bash
python -c "
import asyncio
from server import fetch_with_browser

async def test():
    result = await fetch_with_browser('https://example.com')
    print(result)

asyncio.run(test())
"
```

## Troubleshooting

### "playwright not found"
Run `playwright install chromium` after activating the venv.

### Timeout errors
Increase `wait_seconds` for slow-loading pages.

### Still getting blocked?
The server uses multiple anti-detection techniques:
- Chrome's newer headless mode (`--headless=new`)
- Current Chrome user agent (131)
- Realistic HTTP headers (Accept, Sec-Fetch-*, etc.)
- JavaScript stealth (hides `navigator.webdriver`, fake plugins)
- Cookie banner auto-dismissal

For very aggressive sites, you may need to use a different approach (browser extension, manual copy-paste).
