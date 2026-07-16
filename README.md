# PatchContext

PatchContext is a RAG pipeline over the FastAPI repository's commit history, pull requests, and issue threads. It lets engineers ask "why was this designed this way?" and get answers grounded in developer discussions, with clickable citations to commit SHAs, PR numbers, and issue IDs.

It uses LangChain, FAISS, OpenAI `text-embedding-ada-002`, `gpt-4o-mini`, MMR retrieval for source diversity, a citation/NLI hallucination guard, a Streamlit UI, and RAGAs evaluation on a 50-question benchmark.

## What You Build

- GitHub ingestion for `fastapi/fastapi` commits, pull requests, issues, and comments.
- Normalized JSONL document store with stable citation metadata.
- FAISS vector index using OpenAI embeddings.
- MMR retriever via LangChain.
- Grounded answer generation with clickable GitHub citations.
- Hallucination guard that blocks fabricated citations and, when enabled, runs an MNLI entailment check.
- Streamlit UI for interactive questions.
- RAGAs benchmark harness with 50 seed questions.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Fill OPENAI_API_KEY and optionally GITHUB_TOKEN.
```

Ingest GitHub history:

```bash
patchcontext-ingest --repo fastapi/fastapi --max-pages 20
```

Build the FAISS index:

```bash
patchcontext-index
```

Run the UI:

```bash
streamlit run app.py
```

Ask from the terminal:

```bash
patchcontext-ask "Why was dependency injection designed around Depends?"
```

Run evaluation:

```bash
patchcontext-eval --questions benchmark/questions.jsonl --out outputs/ragas_results.json
```

## Notes

- Use `GITHUB_TOKEN` for reliable ingestion. Without it, GitHub API rate limits are low.
- `--max-pages` controls how much history you ingest. Remove it for a deeper run.
- The default guard always validates citations against retrieved sources. Set `PATCHCONTEXT_ENABLE_NLI=1` for the NLI support check.
- Install the optional NLI dependencies with `pip install -e ".[nli]"`.
- The benchmark includes question templates. For rigorous reporting, curate expected ground-truth answers after the full corpus is ingested.

## Architecture

PatchContext follows an advanced RAG pattern designed for robust code-history queries:

1. **Ingestion & Indexing**: Commits, PRs, and Issue threads are downloaded from GitHub, aggregated into unified JSONL files, chunked, and embedded into a local **FAISS Vector Store** using `text-embedding-ada-002`.
2. **Diverse Retrieval**: Uses **Maximal Marginal Relevance (MMR)** to fetch documents that are highly relevant but semantically diverse, preventing duplicate discussions from overwhelming the context window.
3. **Synthesis**: Answers are generated using `gpt-4o-mini` (or `llama-3.3-70b-versatile` if a Groq fallback is detected) via LangChain.
4. **Hallucination Guard**: A dual-check guard validates that (a) any cited commit SHA or PR actually exists in the retrieved documents, and (b) a zero-shot NLI model (`facebook/bart-large-mnli`) confirms the retrieved documents logically support the generated answer.
5. **Presentation**: Results are shown either in the terminal (`patchcontext-ask`) or the interactive Streamlit dashboard (`app.py`), complete with dynamic, clickable GitHub citations.

## Evaluation

PatchContext is continuously tested using the **RAGAs** (Retrieval Augmented Generation Assessment) framework against a 50-question benchmark (`benchmark/questions.jsonl`). 

To run the evaluation pipeline and generate precision, recall, answer relevancy, and faithfulness metrics, execute:
```bash
patchcontext-eval --questions benchmark/questions.jsonl --out outputs/ragas_results.json
```
The output report is saved to `outputs/ragas_results.summary.json`, allowing you to objectively verify pipeline improvements.
