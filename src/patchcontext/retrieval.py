from __future__ import annotations

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from patchcontext.config import get_settings
from patchcontext.embeddings import get_embeddings


def load_vectorstore() -> FAISS:
    settings = get_settings()
    return FAISS.load_local(
        str(settings.index_dir),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def retrieve(question: str, *, k: int = 8, fetch_k: int = 32) -> list[Document]:
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": fetch_k, "lambda_mult": 0.45},
    )
    return list(retriever.invoke(question))


def format_context(docs: list[Document]) -> str:
    blocks: list[str] = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        label = meta.get("citation_label") or meta.get("id") or f"source-{i}"
        blocks.append(
            f"[{i}] {label} | {meta.get('source_type')} | {meta.get('url')}\n"
            f"Title: {meta.get('title')}\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(blocks)
