# Walkthrough - Running PatchContext RAG Application

This document details how the project was successfully run and verified.

## Accomplishments

1. **Groq API Key Integration**:
   - The `.env` file contained a Groq API key (`gsk_...`) under `OPENAI_API_KEY`. This was causing `401 - Incorrect API key` errors when trying to call OpenAI's embedding API.
   - We updated [embeddings.py](src/patchcontext/embeddings.py) to automatically fall back to the deterministic `HashEmbeddings` when a Groq key (`gsk_...`) is configured.
   - We updated [answer.py](src/patchcontext/answer.py) to route the LLM synthesis component through Groq's OpenAI-compatible endpoint (`https://api.groq.com/openai/v1`) using the high-performance `llama-3.3-70b-versatile` model.

2. **CLI Query Verification**:
   - Ran `patchcontext-ask` to query: *"What was the fix for the race condition in _IncludedRouter cache rebuild?"*
   - Verification succeeded and returned correct, grounded answers citing `PR #15977` and `Issue #15974`.

3. **Streamlit App Launch**:
   - Started the Streamlit UI server in the background:
     ```bash
     .venv/bin/streamlit run app.py
     ```
   - Streamlit is running successfully on **`http://localhost:8503`**.

4. **UI Verification**:
   - A browser subagent verified the Streamlit web application.
   - The subagent successfully typed queries into the UI, clicked the **Ask** button, and retrieved grounded responses citing source GitHub pull requests and commits.

## Video Demonstration

Below is the recorded browser interaction of our query run:

![Verification Recording](/Users/admin/.gemini/antigravity-ide/brain/e04680bc-d680-4153-b30e-ed4c2b48e194/streamlit_ui_query_1783828304412.webp)

---

The Streamlit app will remain running in the background. You can open and interact with it at:
👉 **[http://localhost:8503](http://localhost:8503)**
