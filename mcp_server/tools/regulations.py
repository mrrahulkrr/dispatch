import os
import httpx
from .utils import get_async_client
from typing import Optional, Dict, Any

async def search_regulations(query: str, agency: Optional[str] = None, comment_period_open: Optional[bool] = None) -> Dict[str, Any]:
    api_key = os.getenv("REGULATIONS_GOV_API_KEY")
    if not api_key:
        raise ValueError("REGULATIONS_GOV_API_KEY environment variable is missing")
        
    url = "https://api.regulations.gov/v4/documents"
    headers = {"X-Api-Key": api_key}
    params: Dict[str, Any] = {"filter[searchTerm]": query}
    if agency:
        params["filter[agencyId]"] = agency
    if comment_period_open is not None:
        params["filter[commentEndDate]"] = "Open" if comment_period_open else "Closed"
        
    async with get_async_client(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Regulations API error: {e.response.status_code} - {e.response.text}")

async def get_docket_comments(docket_id: str) -> Dict[str, Any]:
    api_key = os.getenv("REGULATIONS_GOV_API_KEY")
    if not api_key:
        raise ValueError("REGULATIONS_GOV_API_KEY environment variable is missing")
        
    url = "https://api.regulations.gov/v4/comments"
    headers = {"X-Api-Key": api_key}
    params = {"filter[searchTerm]": docket_id}
    
    async with get_async_client(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Regulations API error: {e.response.status_code} - {e.response.text}")
