import os
import sys
import uuid
import json
import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict

from dotenv import load_dotenv
load_dotenv(".env.local")

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

# US Section Configs
from backend.sections.policy_radar.config import policy_radar_config
from backend.sections.research_radar.config import research_radar_config
from backend.sections.markets_radar.config import markets_radar_config

# UK Section Configs
from backend.sections.uk_policy_radar.config import uk_policy_radar_config
from backend.sections.uk_markets_radar.config import uk_markets_radar_config

# Canada, EU, India Configs
from backend.sections.canada_policy_radar.config import canada_policy_radar_config
from backend.sections.eu_policy_radar.config import eu_policy_radar_config
from backend.sections.india_markets_radar.config import india_markets_radar_config

from backend.graph.graph import build_graph
from backend.db.session import SessionLocal, init_db
from backend.db.models import Digest

# ---------------------------------------------------------
# Region & Config Registry
# ---------------------------------------------------------
REGIONS = {
    "US": {"name": "United States", "flag": "🇺🇸"},
    "UK": {"name": "United Kingdom", "flag": "🇬🇧"},
    "EU": {"name": "European Union", "flag": "🇪🇺"},
    "CA": {"name": "Canada", "flag": "🇨🇦"},
    "IN": {"name": "India", "flag": "🇮🇳"},
}

ALL_CONFIGS = [
    # US
    policy_radar_config,
    research_radar_config,
    markets_radar_config,
    # UK
    uk_policy_radar_config,
    uk_markets_radar_config,
    # Canada
    canada_policy_radar_config,
    # EU
    eu_policy_radar_config,
    # India
    india_markets_radar_config,
]

# Build nested lookup: CONFIGS[region][slug] = config
CONFIGS: Dict[str, Dict[str, Any]] = defaultdict(dict)
for conf in ALL_CONFIGS:
    CONFIGS[conf.region][conf.slug] = conf

# Flat lookup for backward compatibility
FLAT_CONFIGS = {conf.slug: conf for conf in ALL_CONFIGS}

# Global checkpointer and graph pool
checkpointer = None
graphs = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate required environment variables
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is missing. Check your .env.local file.", file=sys.stderr)
        sys.exit(1)
        
    has_llm = any([os.getenv("GEMINI_API_KEY"), os.getenv("GROQ_API_KEY"), os.getenv("OPENROUTER_API_KEY")])
    if not has_llm:
        print("ERROR: No LLM API Key provided. You must set GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY in .env.local.", file=sys.stderr)
        sys.exit(1)

    global checkpointer, graphs
    init_db()
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Remove channel_binding param (not supported by psycopg conninfo)
    if "channel_binding" in db_url:
        import re
        db_url = re.sub(r'[&?]channel_binding=[^&]*', '', db_url)
        
    pool = AsyncConnectionPool(conninfo=db_url, max_size=20, open=False, kwargs={"autocommit": True})
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    
    # Initialize graphs for ALL sections across ALL regions
    for conf in ALL_CONFIGS:
        graphs[conf.slug] = build_graph(conf, checkpointer=checkpointer)
        
    yield
    
    await pool.close()

app = FastAPI(lifespan=lifespan)

# CORS — Allow Streamlit Cloud frontend to call the Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    watch_topic: str

class EditRequest(BaseModel):
    digest_draft: List[Dict[str, Any]]

# ---------------------------------------------------------
# Region Endpoints (NEW)
# ---------------------------------------------------------
@app.get("/regions")
async def list_regions():
    """List all available regions with their agents."""
    result = []
    for region_code, region_meta in REGIONS.items():
        agents = []
        for slug, conf in CONFIGS.get(region_code, {}).items():
            agents.append({
                "slug": conf.slug,
                "name": conf.name,
                "description": conf.description,
                "default_topics": conf.default_topics
            })
        result.append({
            "code": region_code,
            "name": region_meta["name"],
            "flag": region_meta["flag"],
            "agents": agents
        })
    return result

@app.get("/regions/{region}/sections")
async def list_region_sections(region: str):
    """List agents for a specific region."""
    region = region.upper()
    if region not in REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    return [
        {"slug": c.slug, "name": c.name, "description": c.description, "default_topics": c.default_topics}
        for c in CONFIGS.get(region, {}).values()
    ]

@app.post("/regions/{region}/sections/{slug}/runs")
async def start_region_run(region: str, slug: str, req: RunRequest):
    """Start a run for an agent in a specific region."""
    region = region.upper()
    if region not in REGIONS or slug not in CONFIGS.get(region, {}):
        raise HTTPException(status_code=404, detail="Region or section not found")
    
    if slug not in graphs:
        raise HTTPException(status_code=404, detail="Graph not initialized for this section")
        
    graph = graphs[slug]
    run_id = f"{slug}:{uuid.uuid4()}"
    config = {"configurable": {"thread_id": run_id}}
    
    state_input = {
        "section_slug": slug,
        "watch_topic": req.watch_topic
    }
    
    result = await graph.ainvoke(state_input, config)
    
    return {
        "run_id": run_id,
        "status": "completed",
        "synthesis": result.get("synthesis", ""),
        "digest_draft": result.get("digest_draft", [])
    }

@app.get("/regions/{region}/sections/{slug}/digests")
async def list_region_digests(region: str, slug: str):
    """List digests for an agent in a specific region."""
    region = region.upper()
    if region not in REGIONS or slug not in CONFIGS.get(region, {}):
        raise HTTPException(status_code=404, detail="Region or section not found")
    
    db = SessionLocal()
    try:
        digests = db.query(Digest).filter(Digest.section_slug == slug).all()
        return [
            {
                "id": str(d.id),
                "thread_id": d.thread_id,
                "watch_topic": d.watch_topic,
                "synthesis": d.synthesis,
                "digest_draft": d.digest_draft,
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None
            }
            for d in digests
        ]
    finally:
        db.close()

@app.get("/regions/{region}/evals/{slug}")
async def get_region_evals(region: str, slug: str):
    """Get evaluation results for an agent in a specific region."""
    region = region.upper()
    if region not in REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    
    results_file = f"backend/evals/eval_results_{slug}.json"
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            return json.load(f)
    return {"error": "Evals not run yet for this section."}

# ---------------------------------------------------------
# Legacy Endpoints (backward compatible — default to US)
# ---------------------------------------------------------
@app.get("/sections")
async def list_sections():
    return [{"slug": c.slug, "name": c.name, "description": c.description, "default_topics": c.default_topics, "region": c.region} for c in ALL_CONFIGS]

@app.post("/sections/{slug}/runs")
async def start_run(slug: str, req: RunRequest):
    if slug not in graphs:
        raise HTTPException(status_code=404, detail="Section not found")
        
    graph = graphs[slug]
    run_id = f"{slug}:{uuid.uuid4()}"
    config = {"configurable": {"thread_id": run_id}}
    
    state_input = {
        "section_slug": slug,
        "watch_topic": req.watch_topic
    }
    
    result = await graph.ainvoke(state_input, config)
    
    return {
        "run_id": run_id,
        "status": "completed",
        "synthesis": result.get("synthesis", ""),
        "digest_draft": result.get("digest_draft", [])
    }

@app.get("/sections/{slug}/runs/{run_id}")
async def get_run(slug: str, run_id: str):
    if slug not in graphs:
        raise HTTPException(status_code=404, detail="Section not found")
    
    config = {"configurable": {"thread_id": run_id}}
    state = await graphs[slug].aget_state(config)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return state.values

@app.get("/sections/{slug}/digests")
async def list_digests(slug: str):
    db = SessionLocal()
    try:
        digests = db.query(Digest).filter(Digest.section_slug == slug).all()
        return [
            {
                "id": str(d.id),
                "thread_id": d.thread_id,
                "watch_topic": d.watch_topic,
                "synthesis": d.synthesis,
                "digest_draft": d.digest_draft,
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None
            }
            for d in digests
        ]
    finally:
        db.close()

@app.get("/evals/{slug}")
async def get_evals(slug: str):
    results_file = f"backend/evals/eval_results_{slug}.json"
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            return json.load(f)
    return {"error": "Evals not run yet for this section."}
