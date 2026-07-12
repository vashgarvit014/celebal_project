# Project Audit - PatchContext RAG Compliance Report

This audit checks each requirement of PatchContext to verify that all design criteria are satisfied and correctly implemented in the codebase.

---

## 📋 Compliance Checklist

| Feature Requirement | Status | Verification & Code References |
| :--- | :--- | :--- |
| **GitHub Ingestion** (Commits, PRs, Issues, and Comments) | **Fulfilled** | Commits and Issues/PRs are fetched from GitHub, including comments and merge metadata: <br> - [ingest_commits](src/patchcontext/ingest.py#L15) <br> - [ingest_issues_and_prs](src/patchcontext/ingest.py#L54) |
| **Grounded Developer Discussions** | **Fulfilled** | Discussion details are fetched using GitHub Issue comments and concatenated into the document context: <br> - [Comments extraction](src/patchcontext/ingest.py#L71-L86) |
| **Clickable Citations** (Commit SHAs, PRs, Issue IDs) | **Fulfilled** | Document metadata maps URLs and citation labels, which are formatted as clickable links in the Streamlit UI and CLI: <br> - [citation_label getter](src/patchcontext/models.py#L25-L33) <br> - [Streamlit source links](app.py#L43-L45) |
| **LangChain Core Integration** | **Fulfilled** | Utilized for vector store wrappers, embeddings, chat LLM wrapping, and retriever orchestration: <br> - [embeddings.py](src/patchcontext/embeddings.py) <br> - [retrieval.py](src/patchcontext/retrieval.py) |
| **FAISS Vector Index** | **Fulfilled** | Vector indexing and local saving/loading are fully implemented using FAISS: <br> - [FAISS save](src/patchcontext/index.py#L57-L59) <br> - [FAISS load](src/patchcontext/retrieval.py#L10-L16) |
| **OpenAI text-embedding-ada-002** | **Fulfilled** | Configured as default embedding model, with deterministic `HashEmbeddings` fallback for local/offline testing: <br> - [embedding_model default](src/patchcontext/config.py#L19) <br> - [OpenAIEmbeddings builder](src/patchcontext/embeddings.py#L38-L40) |
| **gpt-4o-mini LLM Synthesis** | **Fulfilled** | Configured as default chat model, with smart Groq endpoint fallback (`llama-3.3-70b-versatile`) when key starts with `gsk_`: <br> - [chat_model default](src/patchcontext/config.py#L20) <br> - [ChatOpenAI initialization](src/patchcontext/answer.py#L62-L72) |
| **MMR Retrieval for Result Diversity** | **Fulfilled** | Retriever queries the vector store utilizing MMR to enforce diverse result retrieval: <br> - [retrieve using MMR](src/patchcontext/retrieval.py#L21-L24) |
| **NLI Hallucination Guard** | **Fulfilled** | Implemented using a dual check: citation verification first, followed by a local MNLI model entailment check via transformers: <br> - [validate_citations](src/patchcontext/guard.py#L37-L53) <br> - [NLIGuard model check](src/patchcontext/guard.py#L56-L91) |
| **Streamlit Interactive UI** | **Fulfilled** | Fully functional Streamlit front-end allowing users to query, set parameters, and read grounded answers with source citations: <br> - [app.py](app.py) |
| **RAGAs 50-Question Benchmark** | **Fulfilled** | Configured with a JSONL dataset containing exactly 50 target questions, and integrated with the evaluation pipeline: <br> - [evaluate.py](src/patchcontext/evaluate.py) <br> - [questions.jsonl](benchmark/questions.jsonl) |

---

## 🔍 Detail Audit Findings

### 1. Ingestion & Discussion Context
*   **Source**: [ingest.py](src/patchcontext/ingest.py)
*   **Result**: The ingestion pipeline fetches commits via `/commits` and issues/PRs via `/issues`, which natively includes pull requests in GitHub's REST API. It resolves PR merge details (such as merge commit hashes and branch refs) and comment threads to make sure actual developer discussions are captured inside the vector space.

### 2. Citations & Links
*   **Source**: [models.py](src/patchcontext/models.py) & [app.py](app.py)
*   **Result**: Citation labels (e.g. `PR #123`, `Issue #456`, or short commit SHA) are generated dynamically. Streamlit uses Markdown links to render these citations as clickable items pointing directly to the corresponding GitHub URLs.

### 3. Retrieval (FAISS & MMR)
*   **Source**: [retrieval.py](src/patchcontext/retrieval.py)
*   **Result**: Retrieves documents utilizing Maximal Marginal Relevance (`search_type="mmr"`). Setting `lambda_mult=0.45` enforces a robust diversity-relevance balance, preventing duplicate code or comment snippets from crowding the prompt window.

### 4. Hallucination Guard
*   **Source**: [guard.py](src/patchcontext/guard.py)
*   **Result**:
    1.  `validate_citations` extracts citations from the LLM answer using regex and compares them to the source metadata. If the LLM generates a fake commit SHA or reference not present in the search context, it blocks the answer.
    2.  `NLIGuard` (when enabled via `PATCHCONTEXT_ENABLE_NLI=1`) loads `facebook/bart-large-mnli` to perform a zero-shot support classification. If the hypothesis contradicts the retrieved premise, it triggers the guard failure.

### 5. Evaluation Harness
*   **Source**: [evaluate.py](src/patchcontext/evaluate.py) & [questions.jsonl](benchmark/questions.jsonl)
*   **Result**: Integrates RAGAs metrics (`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`) to perform batch runs over the 50 pre-populated questions.
