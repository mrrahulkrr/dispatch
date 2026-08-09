import uuid
import json
import logging
from datetime import datetime
from typing import Any, Dict

from langgraph.types import interrupt

from backend.graph.state import DispatchState
from backend.sections.base import SectionConfig
from backend.llm.llm_client import generate_text, get_embeddings, cosine_similarity
from backend.db.session import SessionLocal
from backend.db.models import Digest

from mcp_server.tools.congress import search_bills, get_bill_detail
from mcp_server.tools.regulations import search_regulations, get_docket_comments
from mcp_server.tools.federal_register import search_federal_register, search_presidential_documents
from mcp_server.tools.arxiv import search_arxiv
from mcp_server.tools.sec import search_sec_filings

# UK Tools
from mcp_server.tools.uk_parliament import search_uk_bills, get_uk_bill_detail
from mcp_server.tools.uk_legislation import search_uk_legislation, search_uk_statutory_instruments
from mcp_server.tools.companies_house import search_companies_house

# Canada, EU, India Tools
from mcp_server.tools.canada_parliament import search_canada_bills
from mcp_server.tools.eu_journal import search_eu_official_journal
from mcp_server.tools.india_markets import search_nse_announcements

logger = logging.getLogger(__name__)

TOOL_REGISTRY = {
    # US Tools
    "search_bills": search_bills,
    "get_bill_detail": get_bill_detail,
    "search_regulations": search_regulations,
    "get_docket_comments": get_docket_comments,
    "search_federal_register": search_federal_register,
    "search_presidential_documents": search_presidential_documents,
    "search_arxiv": search_arxiv,
    "search_sec_filings": search_sec_filings,
    # UK Tools
    "search_uk_bills": search_uk_bills,
    "get_uk_bill_detail": get_uk_bill_detail,
    "search_uk_legislation": search_uk_legislation,
    "search_uk_statutory_instruments": search_uk_statutory_instruments,
    "search_companies_house": search_companies_house,
    # Canada, EU, India
    "search_canada_bills": search_canada_bills,
    "search_eu_official_journal": search_eu_official_journal,
    "search_nse_announcements": search_nse_announcements,
}

def _normalize_search_results(result: dict) -> list[dict]:
    """Helper to normalize raw tool outputs into a standard document format."""
    normalized = []
    
    if "bills" in result:
        for b in result["bills"]:
            normalized.append({
                "id": str(b.get("number", uuid.uuid4())),
                "source": "congress",
                "title": b.get("title", "No Title"),
                "date": b.get("updateDate", ""),
                "url": b.get("url", ""),
                "raw_text": json.dumps(b)
            })
    elif "uk_bills" in result:
        for b in result["uk_bills"]:
            normalized.append({
                "id": str(b.get("billId", uuid.uuid4())),
                "source": "uk_parliament",
                "title": b.get("title", "No Title"),
                "date": b.get("lastUpdate", ""),
                "url": b.get("url", ""),
                "raw_text": f"{b.get('title', '')}\n{b.get('summary', '')}\nHouse: {b.get('currentHouse', '')}\nIs Act: {b.get('isAct', False)}\n{json.dumps(b)}"
            })
    elif "data" in result:
        for d in result["data"]:
            attrs = d.get("attributes", {})
            normalized.append({
                "id": d.get("id", str(uuid.uuid4())),
                "source": "regulations",
                "title": attrs.get("title", "No Title"),
                "date": attrs.get("lastModifiedDate", ""),
                "url": attrs.get("fileUrl", f"https://www.regulations.gov/document/{d.get('id')}"),
                "raw_text": json.dumps(attrs)
            })
    elif "results" in result:
        source_hint = result.get("source", "")
        for r in result["results"]:
            doc_id = r.get("document_number") or r.get("id") or r.get("company_number") or str(uuid.uuid4())
            title = r.get("title", "No Title")
            date = r.get("publication_date") or r.get("published") or r.get("updated") or r.get("date_of_creation", "")
            url = r.get("html_url") or r.get("link") or r.get("url", "")
            abstract = r.get("abstract") or r.get("summary") or r.get("address", "")
            
            if "legislation.gov.uk" in source_hint:
                source = "uk_legislation"
            elif "company_number" in r:
                source = "companies_house"
            elif "summary" in r and "link" in r:
                source = "arxiv"
            else:
                source = "federal_register"
            
            normalized.append({
                "id": doc_id,
                "source": source,
                "title": title,
                "date": date,
                "url": url,
                "raw_text": str(abstract) + "\n" + json.dumps(r)
            })
    elif "canada_bills" in result:
        for b in result["canada_bills"]:
            normalized.append({
                "id": str(b.get("number", uuid.uuid4())),
                "source": "canada_parliament",
                "title": b.get("title", "No Title"),
                "date": b.get("session", ""),
                "url": b.get("url", ""),
                "raw_text": f"{b.get('title', '')}\nStatus: {b.get('status', '')}\n{json.dumps(b)}"
            })
    elif "eu_journal_entries" in result:
        for j in result["eu_journal_entries"]:
            normalized.append({
                "id": str(uuid.uuid4()),
                "source": "eu_journal",
                "title": j.get("title", "No Title"),
                "date": j.get("published", ""),
                "url": j.get("link", ""),
                "raw_text": f"{j.get('title', '')}\n{j.get('description', '')}"
            })
    elif "nse_announcements" in result:
        for a in result["nse_announcements"]:
            normalized.append({
                "id": str(uuid.uuid4()),
                "source": "nse_india",
                "title": f"{a.get('symbol', 'UNKNOWN')} - {a.get('subject', 'No Subject')}",
                "date": a.get("broadcast_date", ""),
                "url": a.get("attachment", ""),
                "raw_text": f"Company: {a.get('company_name', '')}\nSubject: {a.get('subject', '')}\nDetails: {a.get('details', '')}"
            })
            
    return normalized

async def ingest(state: DispatchState, section_config: SectionConfig) -> dict[str, Any]:
    raw_docs = []
    search_tools = [t for t in section_config.mcp_tools if t.startswith("search_")]
    
    for tool_name in search_tools:
        if tool_name not in TOOL_REGISTRY:
            logger.warning(f"Tool {tool_name} not found in registry")
            continue
            
        tool_fn = TOOL_REGISTRY[tool_name]
        try:
            result = await tool_fn(query=state.watch_topic)
            raw_docs.extend(_normalize_search_results(result))
        except Exception as e:
            logger.error(f"Error calling {tool_name}: {e}")
            continue
            
    return {"raw_docs": state.raw_docs + raw_docs}

async def classify(state: DispatchState, section_config: SectionConfig) -> dict[str, Any]:
    classified_docs = []
    
    if not state.raw_docs:
        return {"classified_docs": []}
    
    topic_emb = (await get_embeddings([state.watch_topic]))[0]
    texts_to_embed = [d["title"] + "\n" + d["raw_text"][:500] for d in state.raw_docs]
    doc_embs = await get_embeddings(texts_to_embed)
    
    threshold = 0.5
    pre_filtered = []
    for doc, emb in zip(state.raw_docs, doc_embs):
        sim = cosine_similarity(topic_emb, emb)
        if sim > threshold:
            pre_filtered.append(doc)
            
    for doc in pre_filtered:
        prompt = (
            f"Watch Topic: {state.watch_topic}\n"
            f"Classification Rules: {section_config.classify_prompt}\n\n"
            f"Document Title: {doc['title']}\n"
            f"Document Text: {doc['raw_text'][:2000]}\n\n"
            "Return JSON with {relevant: bool, relevance_score: float, reason: str}"
        )
        try:
            resp = await generate_text(prompt, system_instruction="You are a strict JSON classification engine. Output only JSON.", provider_pref="groq")
            resp = resp.strip().strip('```json').strip('```').strip()
            parsed = json.loads(resp)
            doc_info = dict(doc)
            doc_info.update(parsed)
            if parsed.get("relevant"):
                classified_docs.append(doc_info)
        except Exception as e:
            logger.warning(f"Classify LLM error on doc {doc['id']}: {e}")
            
    logger.info(f"Classify: {len(state.raw_docs)} raw -> {len(pre_filtered)} after embeddings -> {len(classified_docs)} after LLM")
    
    return {"classified_docs": state.classified_docs + classified_docs}

async def summarize(state: DispatchState, section_config: SectionConfig) -> dict[str, Any]:
    summaries = []
    for doc in state.classified_docs:
        prompt = (
            f"Document Title: {doc['title']}\n"
            f"Document URL: {doc['url']}\n"
            f"Document Text: {doc['raw_text'][:4000]}\n\n"
            f"Style: {section_config.summary_style}\n\n"
            "Rule: Every factual claim must be traceable to a specific passage in the raw text. Include the source URL."
        )
        try:
            summary_text = await generate_text(prompt, system_instruction="You are a meticulous summarizer.")
            summaries.append({
                "id": doc["id"],
                "title": doc["title"],
                "url": doc["url"],
                "summary": summary_text
            })
        except Exception as e:
            logger.warning(f"Summarize LLM error on doc {doc['id']}: {e}")
            
    return {"summaries": state.summaries + summaries}

async def impact_analyst(state: DispatchState, section_config: SectionConfig) -> dict[str, Any]:
    digest_draft = []
    for s in state.summaries:
        prompt = (
            f"Watch Topic: {state.watch_topic}\n"
            f"Summary: {s['summary']}\n\n"
            "Produce a one-paragraph 'why this matters to you' impact note tailored to the watch topic."
        )
        try:
            impact_note = await generate_text(prompt, system_instruction="You are an impact analyst.")
            digest_draft.append({
                "summary": s["summary"],
                "impact_note": impact_note,
                "source_url": s["url"]
            })
        except Exception as e:
            logger.warning(f"Impact LLM error on summary {s['id']}: {e}")
            
    return {"digest_draft": digest_draft}
async def synthesize(state: DispatchState, section_config: SectionConfig) -> dict[str, Any]:
    if not state.digest_draft:
        return {"synthesis": "No relevant documents found to synthesize."}
        
    # Compile all summaries and impact notes for the LLM
    compilation = ""
    for idx, item in enumerate(state.digest_draft):
        compilation += f"\n--- Item {idx+1} ---\nSummary: {item['summary']}\nImpact: {item['impact_note']}\n"
        
    prompt = (
        f"Watch Topic: {state.watch_topic}\n\n"
        f"Here are the summaries and impact notes of the documents found:\n{compilation}\n\n"
        "Write a 1-2 paragraph executive summary that directly answers the watch topic. "
        "Synthesize the key themes, overall direction, and overarching impact across all documents. "
        "Do not list the documents individually; provide a holistic conclusion."
    )
    
    try:
        synthesis = await generate_text(prompt, system_instruction="You are a senior intelligence analyst.")
    except Exception as e:
        logger.warning(f"Synthesize LLM error: {e}")
        synthesis = "Failed to generate synthesis."
        
    return {"synthesis": synthesis}

async def deliver(state: DispatchState, section_config: SectionConfig) -> dict[str, Any]:
    now = datetime.now()
    
    # Determine the thread_id. This depends on how the graph is invoked, 
    # but normally we can generate a new one or pull it from the graph config if possible.
    # LangGraph config gives us thread_id if we have access to it, but state doesn't have it natively.
    # The prompt says: keyed by a thread_id you generate as `f"{section_slug}:{uuid4()}"`.
    # We'll rely on the caller passing it, or generate one if not present, but for DB insert we need it.
    # Actually, let's just use a dummy thread_id if not present, since the router will manage it.
    # We can fetch from config if we had it, but for pure functions we'll just generate a unique one 
    # or require it to be passed.
    # The schema requires thread_id TEXT NOT NULL.
    
    db = SessionLocal()
    try:
        digest = Digest(
            section_slug=state.section_slug,
            thread_id=f"{state.section_slug}-{uuid.uuid4()}", # Fallback thread_id
            watch_topic=state.watch_topic,
            synthesis=state.synthesis,
            digest_draft=state.digest_draft,
            delivered_at=now
        )
        db.add(digest)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to persist digest: {e}")
        db.rollback()
    finally:
        db.close()
        
    return {"delivered_at": now}
