from backend.sections.base import SectionConfig

uk_markets_radar_config = SectionConfig(
    slug="uk-markets-radar",
    name="UK Markets Radar",
    description="Monitors UK Companies House filings and corporate disclosures.",
    region="UK",
    mcp_tools=["search_companies_house"],
    classify_prompt="Determine if the Companies House filing is a significant corporate event (e.g., director change, new incorporation, major filing update).",
    summary_style="Financial analyst brief. 1. Event Summary. 2. Business Impact. 3. Key Details.",
    default_topics=["artificial intelligence", "fintech", "renewable energy"]
)
