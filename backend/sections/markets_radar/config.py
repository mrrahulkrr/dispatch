from backend.sections.base import SectionConfig

markets_radar_config = SectionConfig(
    slug="markets-radar",
    name="Markets Radar",
    description="Monitors SEC EDGAR for recent 8-K and 10-K filings.",
    region="US",
    mcp_tools=["search_sec_filings"],
    classify_prompt="Determine if the SEC filing is a major material event (e.g., leadership change, acquisition, earnings miss).",
    summary_style="Financial analyst brief. 1. Event Summary. 2. Financial Impact. 3. Forward Looking Statement.",
    default_topics=["AAPL", "MSFT"]
)
