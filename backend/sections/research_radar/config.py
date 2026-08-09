from backend.sections.base import SectionConfig

research_radar_config = SectionConfig(
    slug="research-radar",
    name="Research Radar",
    description="Monitors ArXiv for recent scientific papers on specific topics.",
    region="US",
    mcp_tools=["search_arxiv"],
    classify_prompt="Determine if the scientific paper abstract is relevant to the watch topic. Focus on empirical results or novel theoretical models.",
    summary_style="Academic and structured. 1. Core Contribution. 2. Methodology. 3. Results.",
    default_topics=["large language models", "quantum computing"]
)
