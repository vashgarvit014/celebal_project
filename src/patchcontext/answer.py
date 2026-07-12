from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from patchcontext.config import get_settings
from patchcontext.guard import GuardResult, NLIGuard
from patchcontext.retrieval import format_context, retrieve


SYSTEM_PROMPT = """You are PatchContext, a repository-history research assistant.
Answer only from the supplied FastAPI history context. If the context is insufficient,
say what is missing. Cite every concrete claim with source labels that appear in the
context, such as PR #123, Issue #456, or a commit SHA. Do not invent citations."""


@dataclass(frozen=True)
class Source:
    label: str
    title: str
    url: str
    source_type: str


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[Source]
    guard: GuardResult


def sources_from_docs(docs: list[Document]) -> list[Source]:
    seen: set[str] = set()
    sources: list[Source] = []
    for doc in docs:
        meta = doc.metadata
        url = str(meta.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append(
            Source(
                label=str(meta.get("citation_label") or meta.get("id")),
                title=str(meta.get("title") or ""),
                url=url,
                source_type=str(meta.get("source_type") or ""),
            )
        )
    return sources


def answer_question(question: str, *, k: int = 8) -> AnswerResult:
    settings = get_settings()
    docs = retrieve(question, k=k)
    if not settings.openai_api_key:
        answer = extractive_answer(question, docs)
        guard = NLIGuard().check(answer, docs)
        return AnswerResult(answer=answer, sources=sources_from_docs(docs), guard=guard)
    context = format_context(docs)
    if settings.openai_api_key.startswith("gsk_"):
        llm = ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            model="llama-3.3-70b-versatile",
            temperature=0,
        )
    else:
        llm = ChatOpenAI(model=settings.chat_model, temperature=0)
    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                f"Question: {question}\n\nFastAPI history context:\n{context}\n\nGrounded answer:",
            ),
        ]
    )
    answer = str(response.content)
    guard = NLIGuard().check(answer, docs)
    if not guard.passed:
        answer = (
            "I found relevant history, but the generated answer failed the hallucination guard. "
            f"{guard.reason}\n\nTry narrowing the question or ingesting more repository history."
        )
    return AnswerResult(answer=answer, sources=sources_from_docs(docs), guard=guard)


def extractive_answer(question: str, docs: list[Document]) -> str:
    if not docs:
        return "I could not find relevant indexed FastAPI history for that question."
    lines = [
        "Demo mode answer: OPENAI_API_KEY is not set, so I am returning grounded retrieved evidence instead of a generated synthesis.",
        "",
        f"Question: {question}",
        "",
        "Most relevant history:",
    ]
    for doc in docs[:4]:
        meta = doc.metadata
        label = meta.get("citation_label") or meta.get("id")
        excerpt = " ".join(doc.page_content.split())[:500]
        lines.append(f"- {label}: {excerpt}")
    return "\n".join(lines)
