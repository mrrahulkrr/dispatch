import os
import httpx
from .utils import get_async_client
from typing import Optional, Dict, Any

async def search_bills(query: str, congress: Optional[str] = None, chamber: Optional[str] = None) -> Dict[str, Any]:
    api_key = os.getenv("CONGRESS_GOV_API_KEY", "DEMO_KEY")
    
    url = "https://api.govinfo.gov/search"
    
    # We use collection:BILLS to scope to bills.
    search_query = f"collection:BILLS AND {query}"
    if congress:
        search_query += f" AND congress:{congress}"
        
    payload = {
        "query": search_query,
        "pageSize": 10,
        "offsetMark": "*"
    }
    
    params = {"api_key": api_key}
    
    async with get_async_client(timeout=15.0) as client:
        try:
            response = await client.post(url, json=payload, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Map the GovInfo results to the expected format
            mapped_bills = []
            for item in data.get("results", []):
                mapped_bills.append({
                    "number": item.get("packageId"),
                    "title": item.get("title"),
                    "updateDate": item.get("dateIssued"),
                    "url": item.get("detailsLink")
                })
                
            return {"bills": mapped_bills}
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"GovInfo API error: {e.response.status_code} - {e.response.text}")

async def get_bill_detail(bill_id: str) -> Dict[str, Any]:
    # Assume bill_id is in format "{congress}/{billType}/{billNumber}" based on API spec
    api_key = os.getenv("CONGRESS_GOV_API_KEY")
    if not api_key:
        raise ValueError("CONGRESS_GOV_API_KEY environment variable is missing")
    
    url = f"https://api.congress.gov/v3/bill/{bill_id}"
    params = {
        "api_key": api_key,
        "format": "json"
    }
    async with get_async_client(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Congress API error: {e.response.status_code} - {e.response.text}")
