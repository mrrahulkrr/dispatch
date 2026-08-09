from backend.sections.base import SectionConfig

policy_radar_config = SectionConfig(
    slug="policy-radar",
    name="Policy Radar",
    description="Monitors U.S. federal bills, proposed regulations, and Federal Register notices.",
    region="US",
    mcp_tools=[
        "search_bills", "get_bill_detail", 
        "search_regulations", "get_docket_comments",
        "search_federal_register"
    ],
    classify_prompt="The document is relevant if it discusses changes, proposals, or new rules concerning {watch_topic}. It should have a direct impact on policies or regulations.",
    summary_style="Provide a concise, objective summary in a journalistic tone. Focus on the core policy change and its stated justification.",
    default_topics=["artificial intelligence regulation", "climate change policy", "cybersecurity standards"]
)
