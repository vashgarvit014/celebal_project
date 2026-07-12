from __future__ import annotations

import streamlit as st

from patchcontext.answer import answer_question
from patchcontext.config import get_settings


st.set_page_config(page_title="PatchContext", page_icon="PC", layout="wide")

settings = get_settings()

st.title("PatchContext")
st.caption("Ask why FastAPI changed or designed something, with answers grounded in commits, PRs, and issues.")

with st.sidebar:
    st.header("Corpus")
    st.write(f"Repository: `{settings.repo}`")
    st.write(f"Index: `{settings.index_dir}`")
    k = st.slider("Retrieved sources", min_value=4, max_value=16, value=8, step=1)
    st.divider()
    st.write("Build/update the index from the terminal:")
    st.code("patchcontext-ingest --repo fastapi/fastapi\npatchcontext-index", language="bash")

question = st.text_input(
    "Question",
    placeholder="Why was FastAPI's dependency injection designed this way?",
)

if st.button("Ask", type="primary", disabled=not question.strip()):
    with st.spinner("Searching FastAPI history..."):
        try:
            result = answer_question(question, k=k)
        except Exception as exc:  # Streamlit should show actionable setup failures.
            st.error(f"PatchContext failed: {exc}")
        else:
            st.subheader("Answer")
            st.write(result.answer)
            if result.guard.passed:
                st.success(result.guard.reason)
            else:
                st.warning(result.guard.reason)
            st.subheader("Sources")
            for source in result.sources:
                st.markdown(f"- [{source.label}: {source.title}]({source.url}) · `{source.source_type}`")
