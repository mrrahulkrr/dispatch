import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_client(timeout: float = 20.0, follow_redirects: bool = True, extra_headers: dict = None, **kwargs):
    """Provides a configured httpx AsyncClient with standard settings."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)
        
    # If the caller manually passes headers=..., we override the default headers.
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
        
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects, headers=headers, **kwargs) as client:
        yield client
