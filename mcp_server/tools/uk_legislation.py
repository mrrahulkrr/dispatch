import httpx
from .utils import get_async_client
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

ATOM_NS = "{http://www.w3.org/2005/Atom}"
UKLEG_NS = "{http://www.legislation.gov.uk/namespaces/legislation}"

async def _fetch_legislation_feed(feed_url: str, query: str) -> List[Dict[str, Any]]:
    """Fetch and parse a legislation.gov.uk Atom feed, filtering by query keyword."""
    
    async with get_async_client(timeout=15.0) as client:
        try:
            response = await client.get(feed_url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"legislation.gov.uk error: {e.response.status_code}")
    
    root = ET.fromstring(response.text)
    results = []
    query_lower = query.lower()
    
    for entry in root.findall(f"{ATOM_NS}entry"):
        title_el = entry.find(f"{ATOM_NS}title")
        title = title_el.text if title_el is not None else "No Title"
        
        summary_el = entry.find(f"{ATOM_NS}summary")
        summary = summary_el.text if summary_el is not None else ""
        
        link_el = entry.find(f"{ATOM_NS}id")
        url = link_el.text if link_el is not None else ""
        
        updated_el = entry.find(f"{ATOM_NS}updated")
        updated = updated_el.text if updated_el is not None else ""
        
        # Filter by query keyword in title or summary
        if query_lower in (title or "").lower() or query_lower in (summary or "").lower():
            results.append({
                "title": title,
                "summary": summary,
                "url": url,
                "updated": updated,
            })
    
    return results


async def search_uk_legislation(query: str) -> Dict[str, Any]:
    """Search recent UK Acts of Parliament from legislation.gov.uk.
    
    Fetches the Atom feed for UK Public General Acts and filters by query.
    No API key required.
    """
    feed_url = "https://www.legislation.gov.uk/ukpga/data.feed"
    results = await _fetch_legislation_feed(feed_url, query)
    
    return {
        "results": results[:10],
        "source": "legislation.gov.uk (UK Public General Acts)"
    }


async def search_uk_statutory_instruments(query: str) -> Dict[str, Any]:
    """Search recent UK Statutory Instruments from legislation.gov.uk.
    
    Statutory Instruments are secondary legislation (regulations) made under
    powers granted by Acts of Parliament.
    No API key required.
    """
    feed_url = "https://www.legislation.gov.uk/uksi/data.feed"
    results = await _fetch_legislation_feed(feed_url, query)
    
    return {
        "results": results[:10],
        "source": "legislation.gov.uk (UK Statutory Instruments)"
    }
