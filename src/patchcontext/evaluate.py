from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from patchcontext.answer import answer_question
from patchcontext.retrieval import retrieve


def load_questions(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def build_eval_dataset(rows: list[dict[str, str]], limit: int | None = None) -> Dataset:
    records = []
    for row in rows[:limit]:
        question = row["question"]
        docs = retrieve(question, k=8)
        result = answer_question(question, k=8)
        records.append(
            {
                "question": question,
                "answer": result.answer,
                "contexts": [doc.page_content for doc in docs],
                "ground_truth": row.get("ground_truth", ""),
            }
        )
    return Dataset.from_list(records)


def run_evaluation(questions_path: Path, out: Path, limit: int | None = None) -> dict:
    dataset = build_eval_dataset(load_questions(questions_path), limit=limit)
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    
    from langchain_openai import ChatOpenAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from patchcontext.config import get_settings
    
    settings = get_settings()
    llm = ChatOpenAI(
        api_key=settings.openai_api_key, 
        base_url="https://api.groq.com/openai/v1", 
        model="llama-3.3-70b-versatile"
    )
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    result = evaluate(dataset, metrics=metrics, llm=llm, embeddings=embeddings)
    frame = result.to_pandas()
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_json(out, orient="records", indent=2)
    summary = frame.mean(numeric_only=True).to_dict()
    summary_path = out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PatchContext with RAGAs.")
    parser.add_argument("--questions", type=Path, default=Path("benchmark/questions.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("outputs/ragas_results.json"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    summary = run_evaluation(args.questions, args.out, args.limit)
    print(pd.Series(summary).to_string())


if __name__ == "__main__":
    main()

