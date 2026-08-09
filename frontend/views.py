import time
import streamlit as st
import streamlit.components.v1 as components
from frontend.api_client import fetch_sections_for_region, run_research, fetch_digests, fetch_run, fetch_evals
from frontend.components import render_digest_item

def render_welcome_screen():
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <h2>🚀 Welcome to Dispatch</h2>
        <p style="color: #a0aab2; font-size: 1.1rem; max-width: 500px; margin: 0 auto;">
            Your AI-powered intelligence briefing service.<br/>
            Tell us what you want to track, and we'll watch for you 24/7.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 Select a region and agent from the sidebar to get started.")

def render_my_feed():
    st.markdown('<p class="main-header">My Feed</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Latest intelligence from your active agents. What\'s new since you last checked.</p>', unsafe_allow_html=True)
    
    region = st.session_state.selected_region
    sections = fetch_sections_for_region(region)
    
    if not sections:
        render_welcome_screen()
        return

    section_map = {s['name']: s['slug'] for s in sections}
    tabs = st.tabs(list(section_map.keys()))
    
    for i, (name, slug) in enumerate(section_map.items()):
        with tabs[i]:
            if st.button("🔄 Refresh", key=f"refresh_{slug}"):
                st.cache_data.clear()
            
            digests = fetch_digests(region, slug)
            
            if not digests:
                st.info(f"No active reports for {name} yet.")
            else:
                latest = digests[0]
                date_str = latest.get('delivered_at', 'Unknown Date')
                topic = latest.get('watch_topic', 'Unknown Topic')
                
                st.markdown(f"### Latest Intel: **{topic}**")
                st.caption(f"Delivered: {date_str}")
                
                synthesis = latest.get('synthesis')
                if synthesis:
                    st.success(f"**Executive Summary:**\n\n{synthesis}")
                
                drafts = latest.get('digest_draft', [])
                if not drafts:
                    st.info("No highly relevant items found in this run.")
                else:
                    for j, draft in enumerate(drafts):
                        render_digest_item(draft, j, key_prefix=f"feed_{slug}")


def render_research_station():
    st.markdown('<p class="main-header">Research Station</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Run a one-time research query. Pick an agent, enter a topic, and get results.</p>', unsafe_allow_html=True)
    
    region = st.session_state.selected_region
    sections = fetch_sections_for_region(region)
    
    if not sections:
        st.warning("No agents available. Is the backend running?")
        return
        
    section_map = {s['name']: s['slug'] for s in sections}
    
    with st.container(border=True):
        selected_name = st.selectbox("Select Agent", list(section_map.keys()))
        topic = st.text_input("Watch Topic", placeholder="e.g., 'artificial intelligence regulation'")
        
        # Show suggested topics based on selected section
        suggestions = [s.get('suggested_topics', []) for s in sections if s['name'] == selected_name]
        if suggestions and suggestions[0]:
            st.caption(f"💡 Suggested: {', '.join(suggestions[0])}")
            
        if st.button("🔍 Run Research", type="primary"):
            if not topic.strip():
                st.error("Please enter a watch topic.")
            else:
                st.session_state.run_active = True
                st.session_state.run_result = None
                st.session_state.run_cancelled = False
                st.session_state.run_start_time = time.time()
                
                # Kick off thread
                def bg_run():
                    res = run_research(region, section_map[selected_name], topic)
                    if not st.session_state.get('run_cancelled'):
                        st.session_state.run_result = res
                        st.session_state.run_active = False
                
                t = __import__("threading").Thread(target=bg_run)
                from streamlit.runtime.scriptrunner import add_script_run_ctx
                add_script_run_ctx(t)
                t.start()
                st.rerun()

    # Show active state
    if st.session_state.run_active:
        elapsed = time.time() - st.session_state.run_start_time if st.session_state.run_start_time else 0
        st.info(f"⏳ Researching... Time elapsed: {elapsed:.1f}s")
        st.markdown("""
            <div class="glowing-spinner"></div>
            <p style="text-align:center; color:#a0aab2; margin-top:1rem;">
                Our AI agents are currently scouring the data sources, filtering for relevance, 
                and drafting your personalized intelligence brief...
            </p>
        """, unsafe_allow_html=True)
        
        # Fake progress messages
        progress_messages = [
            (0, "Initiating LangGraph workflow..."),
            (2, "Fetching raw documents from MCP Tools..."),
            (5, "Running semantic similarity filter (Embeddings)..."),
            (8, "AI Analysts are evaluating relevance (Groq/Gemini)..."),
            (15, "Drafting executive summary..."),
            (20, "Finalizing report format..."),
            (30, "Taking longer than usual. The government API might be slow...")
        ]
        for threshold, msg in reversed(progress_messages):
            if elapsed >= threshold:
                st.write(msg)
                break
        
        if st.button("❌ Cancel Request", type="secondary"):
            st.session_state.run_cancelled = True
            st.session_state.run_active = False
            st.warning("Request cancelled. Note: the backend may still finish processing in the background.")
            st.stop()
        
        time.sleep(2)
        st.rerun()
    
    if st.session_state.run_cancelled:
        st.warning("Last request was cancelled by user.")
    
    if st.session_state.run_result is not None and not st.session_state.run_cancelled:
        result = st.session_state.run_result
        elapsed = time.time() - st.session_state.run_start_time if st.session_state.run_start_time else 0
        
        if "_error" in result:
            st.error(result["_error"])
        else:
            st.success(f"✅ Research complete! (Took {elapsed:.1f}s) — Run ID: `{result.get('run_id')}`")
            
            drafts = result.get("digest_draft", [])
            st.markdown(f"### Generated Digest ({len(drafts)} items)")
            
            synthesis = result.get("synthesis")
            if synthesis:
                st.success(f"**Executive Summary:**\n\n{synthesis}")
                
            for i, draft in enumerate(drafts):
                render_digest_item(draft, i, key_prefix="research")
        
        if st.button("🔄 Run Another"):
            st.session_state.run_result = None
            st.rerun()


def render_archive():
    st.markdown('<p class="main-header">Archive</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Review past intelligence reports across all agents.</p>', unsafe_allow_html=True)
    
    region = st.session_state.selected_region
    sections = fetch_sections_for_region(region)
    
    if sections:
        all_digests = []
        for s in sections:
            digs = fetch_digests(region, s['slug'])
            for d in digs:
                d['_agent_name'] = s['name']
                d['_agent_slug'] = s['slug']
                all_digests.append(d)
        
        # Simple search/filter
        search_query = st.text_input("🔍 Search Archive (by Topic or Content)", "")
        if search_query:
            search_query = search_query.lower()
            filtered = []
            for d in all_digests:
                if search_query in d.get('watch_topic', '').lower():
                    filtered.append(d)
                elif any(search_query in draft.get('summary', '').lower() for draft in d.get('digest_draft', [])):
                    filtered.append(d)
            all_digests = filtered
        
        all_digests.sort(key=lambda x: x.get('delivered_at', ''), reverse=True)
        
        if not all_digests:
            st.info("No digests found. Run a research query first!")
        else:
            st.write(f"**{len(all_digests)} digests found**")
            for d in all_digests:
                date_str = d.get('delivered_at', 'Unknown Date')
                topic = d.get('watch_topic', 'Unknown Topic')
                agent = d.get('_agent_name', '')
                drafts = d.get('digest_draft', [])
                
                with st.expander(f"📚 {topic} • {agent} • {len(drafts)} items • {date_str[:16]}"):
                    st.caption(f"**Thread ID:** `{d.get('thread_id')}`  •  **DB ID:** `{d.get('id')}`")
                    
                    if st.button("Fetch Raw Run State", key=f"fetch_run_{d.get('id')}"):
                        run_data = fetch_run(d.get('_agent_slug', ''), d.get('thread_id'))
                        if run_data:
                            st.json(run_data)
                            
                    synthesis = d.get('synthesis')
                    if synthesis:
                        st.success(f"**Executive Summary:**\n\n{synthesis}")
                    
                    for i, draft in enumerate(drafts):
                        st.markdown("---")
                        render_digest_item(draft, i, key_prefix=f"archive_{d.get('id')}")
    else:
        st.warning("No agents available. Is the backend running?")


def render_agent_evals():
    st.markdown('<p class="main-header">Agent Evaluations</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Performance metrics and evaluation results for your agents.</p>', unsafe_allow_html=True)
    
    region = st.session_state.selected_region
    sections = fetch_sections_for_region(region)
    
    if sections:
        section_map = {s['name']: s['slug'] for s in sections}
        selected_name = st.selectbox("Select Agent to View Evals", list(section_map.keys()))
        selected_slug = section_map[selected_name]
        
        if st.button("Refresh Evals"):
            st.cache_data.clear()
            
        evals = fetch_evals(region, selected_slug)
        if not evals:
            st.info("No evaluation data found.")
        elif "error" in evals:
            st.info(evals["error"])
        else:
            st.markdown("### Evaluation Results")
            st.json(evals)
    else:
        st.warning("No agents available. Is the backend running?")
