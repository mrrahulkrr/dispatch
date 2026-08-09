import httpx
from .utils import get_async_client
from typing import Dict, Any

async def search_canada_bills(query: str = "", limit: int = 10, session: str = "") -> Dict[str, Any]:
    """Search for Canadian Parliament Bills.
    
    Args:
        query: Search term for bills.
        limit: Max results.
        session: e.g., "44-1" for the 44th Parliament, 1st Session.
    """
    url = "https://api.openparliament.ca/bills/"
    params = {
        "format": "json",
        "limit": limit
    }
    
    # OpenParliament.ca doesn't have a direct full-text search param on this endpoint,
    # but we can fetch recent bills and filter, or use their search endpoint.
    # We will fetch the recent bills list.
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    async with get_async_client(timeout=20.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            bills = []
            objects = data.get("objects", [])
            for item in objects:
                # Basic client-side filtering if query is provided
                name_en = item.get("name", {}).get("en", "").lower()
                short_title_en = item.get("short_title", {}).get("en", "").lower()
                
                if query:
                    q = query.lower()
                    if q not in name_en and q not in short_title_en:
                        continue
                
                bills.append({
                    "number": item.get("number"),
                    "session": item.get("session"),
                    "title": item.get("name", {}).get("en", ""),
                    "short_title": item.get("short_title", {}).get("en", ""),
                    "status": item.get("status", {}).get("en", ""),
                    "law": item.get("law"),
                    "url": f"https://openparliament.ca{item.get('url', '')}"
                })
                
                if len(bills) >= limit:
                    break
                    
            return {"canada_bills": bills, "totalResults": len(bills)}
            
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Canada Parliament API error: {e.response.status_code} - {e.response.text}")
