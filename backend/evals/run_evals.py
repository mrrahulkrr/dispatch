import os
import sys
import json
import asyncio
import argparse

# Fix for windows async
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.sections.policy_radar.config import policy_radar_config
from backend.sections.research_radar.config import research_radar_config
from backend.sections.markets_radar.config import markets_radar_config
from backend.graph.state import DispatchState
from backend.graph.nodes import classify

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", type=str, required=True)
    args = parser.parse_args()
    
    if args.section == "policy-radar":
        config = policy_radar_config
        ds_file = "golden_dataset.json"
    elif args.section == "research-radar":
        config = research_radar_config
        ds_file = "golden_dataset_research.json"
    elif args.section == "markets-radar":
        config = markets_radar_config
        ds_file = "golden_dataset_markets.json"
    else:
        print("Unsupported section")
        return
        
    ds_path = os.path.join(os.path.dirname(__file__), ds_file)
    with open(ds_path, "r") as f:
        ds = json.load(f)
        
    watch_topic = ds["watch_topic"]
    docs = ds["documents"]
    
    # We pass all docs as raw_docs
    state = DispatchState(
        section_slug=args.section,
        watch_topic=watch_topic,
        raw_docs=docs
    )
    
    print(f"Running classify on {len(docs)} golden documents...")
    # classify will use the real LLM and embeddings via llm_client
    result = await classify(state, config)
    
    classified = result.get("classified_docs", [])
    classified_ids = {d["id"] for d in classified if d.get("relevant")}
    
    expected_ids = {d["id"] for d in docs if d["expected_relevant"]}
    
    true_positives = len(classified_ids & expected_ids)
    false_positives = len(classified_ids - expected_ids)
    false_negatives = len(expected_ids - classified_ids)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    metrics = {
        "section": args.section,
        "watch_topic": watch_topic,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }
    
    out_file = os.path.join(os.path.dirname(__file__), f"eval_results_{args.section}.json")
    with open(out_file, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
