.PHONY: install ingest index app eval test

install:
	pip install -e ".[dev]"

ingest:
	patchcontext-ingest --repo fastapi/fastapi --max-pages 20

index:
	patchcontext-index

app:
	streamlit run app.py

eval:
	patchcontext-eval --questions benchmark/questions.jsonl --out outputs/ragas_results.json

test:
	python -m pytest

