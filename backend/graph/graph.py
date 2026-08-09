from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.postgres import PostgresSaver
from backend.graph.state import DispatchState
from backend.sections.base import SectionConfig
from backend.graph.nodes import (
    ingest, classify, summarize, impact_analyst, synthesize, deliver
)
from functools import partial

def build_graph(config: SectionConfig, checkpointer=None):
    workflow = StateGraph(DispatchState)
    
    workflow.add_node("ingest", partial(ingest, section_config=config))
    workflow.add_node("classify", partial(classify, section_config=config))
    workflow.add_node("summarize", partial(summarize, section_config=config))
    workflow.add_node("impact_analyst", partial(impact_analyst, section_config=config))
    workflow.add_node("synthesize", partial(synthesize, section_config=config))
    workflow.add_node("deliver", partial(deliver, section_config=config))
    
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "classify")
    workflow.add_edge("classify", "summarize")
    workflow.add_edge("summarize", "impact_analyst")
    workflow.add_edge("impact_analyst", "synthesize")
    workflow.add_edge("synthesize", "deliver")
    workflow.add_edge("deliver", END)
    
    return workflow.compile(checkpointer=checkpointer)
