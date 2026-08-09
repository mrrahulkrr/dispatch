import httpx
from .utils import get_async_client
from typing import Dict, Any

async def search_nse_announcements(query: str = "", limit: int = 10) -> Dict[str, Any]:
    """Search for corporate announcements and market news related to Indian stocks.
    
    Args:
        query: Specific stock symbol or company name (e.g., 'RELIANCE' or 'SBI').
        limit: Max results.
    """
    # Use Yahoo Finance search API as a reliable alternative to NSE API 
    # (NSE blocks cloud IPs aggressively with 403 Forbidden / Akamai WAF)
    url = f"https://query2.finance.yahoo.com/v1/finance/search"
    
    # If no query provided, use a default Indian market search
    search_query = query if query else "NSE India corporate announcement"
    
    params = {
        "q": search_query,
        "newsCount": limit,
        "quotesCount": 0
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    
    async with get_async_client(timeout=20.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            announcements = []
            
            for item in data.get("news", [])[:limit]:
                announcements.append({
                    "symbol": query.upper() if query else "MARKET",
                    "company_name": item.get("publisher", "Market News"),
                    "subject": item.get("title", "No Title"),
                    "details": f"Published by {item.get('publisher')} - {item.get('providerPublishTime')}",
                    "broadcast_date": str(item.get("providerPublishTime", "")),
                    "attachment": item.get("link", "")
                })
                
            return {"nse_announcements": announcements, "totalResults": len(announcements)}
            
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Market API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch market data: {e}")
