from dataclasses import dataclass

@dataclass
class SectionConfig:
    slug: str
    name: str
    description: str
    region: str  # "US", "UK", "EU", "CA", "IN"
    mcp_tools: list[str]
    classify_prompt: str
    summary_style: str
    default_topics: list[str]
