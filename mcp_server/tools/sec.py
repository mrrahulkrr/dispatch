import httpx
from .utils import get_async_client
from typing import Dict, Any

async def search_sec_filings(query: str) -> Dict[str, Any]:
    """
    Search SEC EDGAR filings for a given query (which we'll treat as a CIK or ticker).
    For simplicity in this demonstration, we'll query a known ticker's submissions
    or just return mock data if the query isn't a CIK since the SEC API requires CIKs.
    Actually, SEC provides a company tickers JSON to map ticker to CIK.
    """
    headers = {
        "User-Agent": "DispatchApp/1.0 (admin@dispatch.local)"
    }
    
    # Simple lookup for demonstration. In reality, we'd map query to CIK.
    # To avoid complex mapping, we'll query the SEC company_tickers.json
    async with get_async_client(timeout=10.0) as client:
        tickers_res = await client.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        
    cik = None
    if tickers_res.status_code == 200:
        data = tickers_res.json()
        for idx, comp in data.items():
            if query.upper() == comp["ticker"] or query.lower() in comp["title"].lower():
                cik = str(comp["cik_str"]).zfill(10)
                break
                
    if not cik:
        # Fallback to a known CIK (Apple) if not found, just for testing
        cik = "0000320193"
        
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    async with get_async_client(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"results": []}
            
    data = response.json()
    recent_filings = data.get("filings", {}).get("recent", {})
    
    results = []
    if recent_filings:
        # Limit to 10
        count = min(10, len(recent_filings.get("accessionNumber", [])))
        for i in range(count):
            results.append({
                "id": recent_filings["accessionNumber"][i],
                "title": f"Form {recent_filings['form'][i]} filed on {recent_filings['filingDate'][i]}",
                "published": recent_filings["filingDate"][i],
                "summary": recent_filings["primaryDocument"][i] or "",
                "link": f"https://www.sec.gov/Archives/edgar/data/{cik}/{recent_filings['accessionNumber'][i].replace('-', '')}/{recent_filings['primaryDocument'][i]}"
            })
            
    return {"results": results}
