import httpx
from .utils import get_async_client
from typing import Optional, Dict, Any

async def search_federal_register(query: str, agency: Optional[str] = None, type: Optional[str] = None, date_range: Optional[str] = None) -> Dict[str, Any]:
    url = "https://www.federalregister.gov/api/v1/articles.json"
    params: Dict[str, Any] = {"conditions[term]": query}
    
    if agency:
        params["conditions[agencies][]"] = agency
    if type:
        params["conditions[type][]"] = type
    if date_range:
        # Expected format for date_range: "YYYY-MM-DD" or similar accepted by the API
        # Often it's conditions[publication_date][gte] etc. We'll pass it simply for now.
        params["conditions[publication_date][gte]"] = date_range
        
    async with get_async_client(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Federal Register API error: {e.response.status_code} - {e.response.text}")

async def search_presidential_documents(query: str, type: Optional[str] = None, date_range: Optional[str] = None) -> Dict[str, Any]:
    url = "https://www.federalregister.gov/api/v1/documents.json"
    params: Dict[str, Any] = {
        "conditions[term]": query,
        "conditions[type][]": "PRESDOCU"
    }
    
    if type:
        params["conditions[presidential_document_type][]"] = type
    if date_range:
        params["conditions[publication_date][gte]"] = date_range
        
    async with get_async_client(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Federal Register API error: {e.response.status_code} - {e.response.text}")
