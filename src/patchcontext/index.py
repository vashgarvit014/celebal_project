from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from patchcontext.config import ensure_dirs, get_settings
from patchcontext.embeddings import get_embeddings
from patchcontext.models import HistoryDocument, read_jsonl


def to_langchain_document(doc: HistoryDocument) -> Document:
    metadata: dict[str, Any] = {
        "id": doc.id,
        "source_type": doc.source_type,
        "title": doc.title,
        "url": doc.url,
        "repo": doc.repo,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "author": doc.author,
        "commit_sha": doc.commit_sha,
        "pr_number": doc.pr_number,
        "issue_number": doc.issue_number,
        "comment_id": doc.comment_id,
        "citation_label": doc.citation_label,
    }
    return Document(page_content=f"{doc.title}\n\n{doc.text}", metadata=metadata)


def chunk_documents(docs: list[HistoryDocument]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=180,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Document] = []
    for doc in docs:
        pieces = splitter.split_documents([to_langchain_document(doc)])
        for index, piece in enumerate(pieces):
            piece.metadata["chunk_id"] = f"{doc.id}:chunk:{index}"
            chunks.append(piece)
    return chunks


def build_index(history_path: Path, index_dir: Path) -> int:
    settings = get_settings()
    ensure_dirs(settings)
    docs = read_jsonl(history_path)
    chunks = chunk_documents(docs)
    if not chunks:
        raise ValueError(f"No documents found in {history_path}")
    vectorstore = FAISS.from_documents(chunks, get_embeddings())
    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))
    return len(chunks)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Build the PatchContext FAISS index.")
    parser.add_argument("--history", type=Path, default=settings.processed_dir / "history.jsonl")
    parser.add_argument("--index-dir", type=Path, default=settings.index_dir)
    args = parser.parse_args()
    count = build_index(args.history, args.index_dir)
    print(f"Indexed {count} chunks into {args.index_dir}")


if __name__ == "__main__":
    main()
