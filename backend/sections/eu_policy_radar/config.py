from backend.sections.base import SectionConfig

eu_policy_radar_config = SectionConfig(
    slug="eu-policy-radar",
    name="Policy Radar",
    description="Monitors the Official Journal of the European Union for new regulations and directives.",
    region="EU",
    mcp_tools=["search_eu_official_journal"],
    classify_prompt="Determine if this EU Official Journal entry is relevant to the watch topic. Focus on regulations, directives, and decisions.",
    summary_style="Provide a concise summary of the EU publication. Include its title, publication date, and the main regulatory impact.",
    default_topics=["artificial intelligence act", "GDPR", "digital markets act"]
)
