import httpx
from .utils import get_async_client
from typing import Optional, Dict, Any

async def search_uk_bills(query: str, current_only: bool = True) -> Dict[str, Any]:
    """Search UK Parliament Bills by keyword.
    
    Uses the official UK Parliament Bills API (free, no auth required).
    Docs: https://developer.parliament.uk/
    """
    url = "https://bills-api.parliament.uk/api/v1/Bills"
    params = {
        "SearchTerm": query,
        "ItemsPerPage": 10,
        "SortOrder": "DateUpdatedDescending"
    }
    if current_only:
        params["CurrentHouse"] = "All"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    async with get_async_client(timeout=20.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            bills = []
            for item in data.get("items", []):
                bills.append({
                    "billId": item.get("billId"),
                    "title": item.get("shortTitle") or item.get("longTitle", "No Title"),
                    "summary": item.get("longTitle", ""),
                    "currentHouse": item.get("currentHouse", ""),
                    "originatingHouse": item.get("originatingHouse", ""),
                    "lastUpdate": item.get("lastUpdate", ""),
                    "isAct": item.get("isAct", False),
                    "billTypeId": item.get("billTypeId"),
                    "url": f"https://bills.parliament.uk/bills/{item.get('billId')}"
                })
            
            return {"uk_bills": bills, "totalResults": data.get("totalResults", 0)}
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"UK Parliament API error: {e.response.status_code} - {e.response.text}")


async def get_uk_bill_detail(bill_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific UK Parliament Bill.
    
    Args:
        bill_id: The numeric bill ID from the Parliament API.
    """
    url = f"https://bills-api.parliament.uk/api/v1/Bills/{bill_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    async with get_async_client(timeout=20.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            return {
                "billId": data.get("billId"),
                "title": data.get("shortTitle") or data.get("longTitle", ""),
                "longTitle": data.get("longTitle", ""),
                "summary": data.get("summary", ""),
                "currentHouse": data.get("currentHouse", ""),
                "originatingHouse": data.get("originatingHouse", ""),
                "lastUpdate": data.get("lastUpdate", ""),
                "isAct": data.get("isAct", False),
                "sponsors": data.get("sponsors", []),
                "promoters": data.get("promoters", []),
                "petitioningPeriod": data.get("petitioningPeriod"),
                "url": f"https://bills.parliament.uk/bills/{data.get('billId')}"
            }
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"UK Parliament API error: {e.response.status_code} - {e.response.text}")
