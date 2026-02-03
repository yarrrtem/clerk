#!/usr/bin/env python3
"""
Headless Browser MCP Server

Fetches web pages using a real browser (Playwright) and extracts
clean article content using trafilatura. Bypasses bot detection
that blocks simple HTTP requests.
"""

import asyncio
import json
import logging
from typing import Optional
from urllib.parse import urlparse

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import trafilatura

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("headless-browser")

# Create the MCP server
server = Server("headless-browser")


def extract_content(html: str, url: str) -> dict:
    """Extract article content from HTML using trafilatura."""

    # Extract main content
    text = trafilatura.extract(
        html,
        include_links=True,
        include_images=False,
        include_tables=True,
        output_format="markdown",
        url=url,
    )

    # Extract metadata
    metadata = trafilatura.extract_metadata(html)

    result = {
        "content": text or "",
        "title": "",
        "author": "",
        "date": "",
        "description": "",
    }

    if metadata:
        result["title"] = metadata.title or ""
        result["author"] = metadata.author or ""
        result["date"] = metadata.date or ""
        result["description"] = metadata.description or ""

    return result


async def fetch_with_browser(url: str, wait_seconds: float = 2.0) -> dict:
    """
    Fetch a URL using a headless browser.

    Args:
        url: The URL to fetch
        wait_seconds: Time to wait for dynamic content to load

    Returns:
        Dict with extracted content and metadata
    """
    async with async_playwright() as p:
        # Launch browser (chromium is most compatible)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--headless=new",  # Use Chrome's newer headless mode
            ]
        )

        # Create context with realistic settings
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            },
        )

        page = await context.new_page()

        # Apply stealth techniques to avoid bot detection
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override navigator.plugins to look real
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Override chrome runtime
            window.chrome = {
                runtime: {}
            };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        try:
            # Navigate to page
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for dynamic content
            await asyncio.sleep(wait_seconds)

            # Try to dismiss cookie banners / popups (common blockers)
            for selector in [
                "button:has-text('Accept')",
                "button:has-text('Got it')",
                "button:has-text('Close')",
                "[aria-label='Close']",
            ]:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=500):
                        await button.click()
                        await asyncio.sleep(0.5)
                except:
                    pass

            # Get the page HTML
            html = await page.content()

            # Get the final URL (in case of redirects)
            final_url = page.url

        finally:
            await browser.close()

        # Extract content
        result = extract_content(html, final_url)
        result["url"] = final_url
        result["original_url"] = url

        return result


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="fetch_url",
            description=(
                "Fetch a web page using a headless browser and extract its content. "
                "Use this for URLs that block normal HTTP requests (e.g., Medium, "
                "paywalled sites, JS-heavy pages). Returns article text in markdown "
                "format along with metadata (title, author, date)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch",
                    },
                    "wait_seconds": {
                        "type": "number",
                        "description": "Seconds to wait for dynamic content (default: 2.0)",
                        "default": 2.0,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="fetch_urls",
            description=(
                "Fetch multiple web pages in parallel using a headless browser. "
                "More efficient than calling fetch_url multiple times."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to fetch",
                    },
                    "wait_seconds": {
                        "type": "number",
                        "description": "Seconds to wait for dynamic content (default: 2.0)",
                        "default": 2.0,
                    },
                },
                "required": ["urls"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "fetch_url":
        url = arguments.get("url")
        wait_seconds = arguments.get("wait_seconds", 2.0)

        if not url:
            return [TextContent(type="text", text="Error: URL is required")]

        try:
            logger.info(f"Fetching URL: {url}")
            result = await fetch_with_browser(url, wait_seconds)

            # Format output
            output_parts = []

            if result["title"]:
                output_parts.append(f"# {result['title']}")

            meta_parts = []
            if result["author"]:
                meta_parts.append(f"**Author:** {result['author']}")
            if result["date"]:
                meta_parts.append(f"**Date:** {result['date']}")
            if result["url"] != result["original_url"]:
                meta_parts.append(f"**Final URL:** {result['url']}")

            if meta_parts:
                output_parts.append("\n".join(meta_parts))

            if result["description"]:
                output_parts.append(f"*{result['description']}*")

            output_parts.append("---")
            output_parts.append(result["content"] or "*No content could be extracted*")

            return [TextContent(type="text", text="\n\n".join(output_parts))]

        except PlaywrightTimeout:
            return [TextContent(type="text", text=f"Error: Timeout while loading {url}")]
        except Exception as e:
            logger.exception(f"Error fetching {url}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "fetch_urls":
        urls = arguments.get("urls", [])
        wait_seconds = arguments.get("wait_seconds", 2.0)

        if not urls:
            return [TextContent(type="text", text="Error: URLs list is required")]

        try:
            logger.info(f"Fetching {len(urls)} URLs")

            # Fetch all URLs in parallel
            tasks = [fetch_with_browser(url, wait_seconds) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Format output
            output_parts = []

            for url, result in zip(urls, results):
                output_parts.append(f"## {url}")
                output_parts.append("")

                if isinstance(result, Exception):
                    output_parts.append(f"*Error: {str(result)}*")
                else:
                    if result["title"]:
                        output_parts.append(f"**{result['title']}**")
                    if result["author"]:
                        output_parts.append(f"Author: {result['author']}")
                    if result["content"]:
                        # Truncate for multi-URL fetches
                        content = result["content"]
                        if len(content) > 2000:
                            content = content[:2000] + "...\n\n*[Content truncated]*"
                        output_parts.append(content)
                    else:
                        output_parts.append("*No content could be extracted*")

                output_parts.append("\n---\n")

            return [TextContent(type="text", text="\n".join(output_parts))]

        except Exception as e:
            logger.exception("Error fetching URLs")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    logger.info("Starting headless-browser MCP server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
