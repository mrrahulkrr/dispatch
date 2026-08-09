from backend.sections.base import SectionConfig

uk_policy_radar_config = SectionConfig(
    slug="uk-policy-radar",
    name="UK Policy Radar",
    description="Monitors UK Parliament bills, Acts of Parliament, and Statutory Instruments.",
    region="UK",
    mcp_tools=[
        "search_uk_bills", "get_uk_bill_detail",
        "search_uk_legislation", "search_uk_statutory_instruments"
    ],
    classify_prompt="The document is relevant if it discusses changes, proposals, or new legislation concerning {watch_topic} in the United Kingdom. It should have a direct impact on UK policy or regulation.",
    summary_style="Provide a concise, objective summary in a journalistic tone. Focus on the core legislative change and its stated justification. Reference UK-specific institutions where applicable.",
    default_topics=["artificial intelligence regulation", "online safety", "data protection"]
)
