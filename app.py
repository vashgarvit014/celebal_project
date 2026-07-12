from __future__ import annotations

import streamlit as st

from patchcontext.answer import answer_question
from patchcontext.config import get_settings


st.set_page_config(page_title="PatchContext", page_icon=":material/quick_reference_all:", layout="wide")

settings = get_settings()

st.title(":material/quick_reference_all: PatchContext", anchor=False)
st.caption("Ask why FastAPI changed or designed something, with answers grounded in commits, PRs, and issues.")

with st.sidebar:
    st.title("Corpus Config")
    st.markdown(f"**Repository:** `{settings.repo}`")
    st.markdown(f"**Index Directory:** `{settings.index_dir}`")
    st.space("medium")
    k = st.slider(
        "Retrieved sources",
        min_value=4,
        max_value=16,
        value=8,
        step=1,
        help="Count of reference documents pulled for synthesis."
    )
    st.space("large")
    with st.container(border=True):
        st.markdown("**:material/sync: Maintenance**")
        st.caption("Rebuild index via terminal:")
        st.code("patchcontext-ingest\npatchcontext-index", language="bash")

st.space("medium")

with st.container(border=True):
    question = st.text_input(
        "Ask a design or history question",
        placeholder="Why was FastAPI's dependency injection designed this way?",
        label_visibility="collapsed",
    )
    ask_btn = st.button("Search Repository History", type="primary", disabled=not question.strip())

if ask_btn:
    with st.spinner("Searching FastAPI history..."):
        try:
            result = answer_question(question, k=k)
        except Exception as exc:  # Streamlit should show actionable setup failures.
            st.error(f"PatchContext failed: {exc}", icon=":material/error:")
        else:
            st.space("medium")
            
            with st.container(border=True):
                col_hdr, col_badge = st.columns([8, 2], vertical_alignment="center")
                with col_hdr:
                    st.markdown("### Grounded Answer")
                with col_badge:
                    if result.guard.passed:
                        st.badge("Guard Passed", icon=":material/verified:", color="green")
                    else:
                        st.badge("Guard Warning", icon=":material/warning:", color="red")
                
                st.write(result.answer)
                
                if not result.guard.passed:
                    st.space("small")
                    st.caption(f":red[{result.guard.reason}]")
            
            st.space("medium")
            
            with st.container(border=True):
                st.markdown("### Citations & Sources")
                for idx, source in enumerate(result.sources, start=1):
                    col_info, col_type = st.columns([8, 2], vertical_alignment="center")
                    with col_info:
                        st.markdown(f"**[{idx}] [{source.label}: {source.title}]({source.url})**")
                    with col_type:
                        st.caption(f"`{source.source_type}`", text_alignment="right")

