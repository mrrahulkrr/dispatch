import os
import httpx
from .utils import get_async_client
from typing import Dict, Any

async def search_companies_house(query: str) -> Dict[str, Any]:
    """Search UK Companies House for company filings and information.
    
    Uses the Companies House API. Requires a free API key from:
    https://developer.company-information.service.gov.uk/
    
    Set COMPANIES_HOUSE_API_KEY environment variable.
    If no key is set, returns a helpful error message.
    """
    api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
    
    if not api_key:
        return {
            "results": [],
            "error": "COMPANIES_HOUSE_API_KEY not set. Get a free key at https://developer.company-information.service.gov.uk/"
        }
    
    url = "https://api.company-information.service.gov.uk/search/companies"
    params = {
        "q": query,
        "items_per_page": 10,
    }
    
    async with get_async_client(timeout=15.0) as client:
        try:
            response = await client.get(url, params=params, auth=(api_key, ""))
            response.raise_for_status()
            data = response.json()
            
            companies = []
            for item in data.get("items", []):
                companies.append({
                    "company_number": item.get("company_number", ""),
                    "title": item.get("title", ""),
                    "company_status": item.get("company_status", ""),
                    "company_type": item.get("company_type", ""),
                    "date_of_creation": item.get("date_of_creation", ""),
                    "address": item.get("address_snippet", ""),
                    "url": f"https://find-and-update.company-information.service.gov.uk/company/{item.get('company_number')}"
                })
            
            return {"results": companies, "total": data.get("total_results", 0)}
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Companies House API error: {e.response.status_code} - {e.response.text}")
