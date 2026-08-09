import streamlit as st

def render_digest_item(draft, index, key_prefix=""):
    """Render a single digest item with summary, impact, source, and feedback buttons."""
    # Determine a source tag if possible based on URL or content
    url = draft.get('source_url', '')
    source_tag = "🔗 External Source"
    if "arxiv.org" in url:
        source_tag = "🏷️ arXiv"
    elif "parliament.uk" in url:
        source_tag = "🏷️ UK Parliament"
    elif "legislation.gov.uk" in url:
        source_tag = "🏷️ UK Legislation"
    elif "congress.gov" in url:
        source_tag = "🏷️ US Congress"
    elif "federalregister.gov" in url:
        source_tag = "🏷️ US Federal Register"
    elif "sec.gov" in url:
        source_tag = "🏷️ SEC EDGAR"
    
    with st.container(border=True):
        st.markdown(f"**{source_tag}**")
        st.markdown(draft.get('summary', 'No summary'))
        
        st.markdown("---")
        st.markdown("**💡 WHY THIS MATTERS**")
        st.info(draft.get('impact_note', 'No impact note'))
        
        st.markdown(f"[View Source Document]({url})")
    
    # Feedback buttons
    col1, col2, col3 = st.columns([1, 1, 6])
    with col1:
        st.button("👍", key=f"{key_prefix}_up_{index}", help="This was useful")
    with col2:
        st.button("👎", key=f"{key_prefix}_dn_{index}", help="Not relevant to my topic")
