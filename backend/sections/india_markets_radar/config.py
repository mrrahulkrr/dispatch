from backend.sections.base import SectionConfig

india_markets_radar_config = SectionConfig(
    slug="india-markets-radar",
    name="Markets Radar",
    description="Monitors the National Stock Exchange of India (NSE) for corporate announcements and disclosures.",
    region="IN",
    mcp_tools=["search_nse_announcements"],
    classify_prompt="Determine if this NSE corporate announcement is relevant to the watch topic. Look for specific company names or industry keywords.",
    summary_style="Provide a structured summary of the corporate announcement, including the company name, subject, and the core details provided.",
    default_topics=["RELIANCE", "TCS", "HDFC"]
)
