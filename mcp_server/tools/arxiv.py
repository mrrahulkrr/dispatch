import httpx
from .utils import get_async_client
from typing import Dict, Any
import xml.etree.ElementTree as ET

async def search_arxiv(query: str, max_results: int = 10) -> Dict[str, Any]:
    # Arxiv API query
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    async with get_async_client(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
    root = ET.fromstring(response.text)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    results = []
    for entry in root.findall('atom:entry', namespace):
        doc = {
            "id": entry.find('atom:id', namespace).text,
            "title": entry.find('atom:title', namespace).text.strip(),
            "published": entry.find('atom:published', namespace).text,
            "summary": entry.find('atom:summary', namespace).text.strip(),
            "link": entry.find('atom:id', namespace).text
        }
        results.append(doc)
        
    return {"results": results}
