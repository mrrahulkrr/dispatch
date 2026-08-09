from backend.sections.base import SectionConfig

canada_policy_radar_config = SectionConfig(
    slug="canada-policy-radar",
    name="Policy Radar",
    description="Monitors Canadian Parliament for new bills, amendments, and legislative updates.",
    region="CA",
    mcp_tools=["search_canada_bills"],
    classify_prompt="Determine if this Canadian bill is relevant to the watch topic. Look for keywords in the title and description.",
    summary_style="Provide a structured summary of the Canadian bill, including its short title, current status, and key regulatory objectives.",
    default_topics=["artificial intelligence", "data privacy", "clean energy"]
)
