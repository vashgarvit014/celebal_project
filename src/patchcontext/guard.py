from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.documents import Document

from patchcontext.config import get_settings


PR_OR_ISSUE = re.compile(r"\b(?:PR|Issue)\s+#(\d+)\b", re.IGNORECASE)
SHA = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)


@dataclass(frozen=True)
class GuardResult:
    passed: bool
    reason: str


def _source_tokens(docs: list[Document]) -> tuple[set[str], set[str]]:
    numbers: set[str] = set()
    shas: set[str] = set()
    for doc in docs:
        meta = doc.metadata
        for key in ("pr_number", "issue_number"):
            if meta.get(key):
                numbers.add(str(meta[key]))
        if meta.get("commit_sha"):
            sha = str(meta["commit_sha"]).lower()
            shas.add(sha)
            shas.add(sha[:7])
            shas.add(sha[:12])
    return numbers, shas


def validate_citations(answer: str, docs: list[Document]) -> GuardResult:
    source_numbers, source_shas = _source_tokens(docs)
    cited_numbers = {match.group(1) for match in PR_OR_ISSUE.finditer(answer)}
    cited_shas = {match.group(0).lower() for match in SHA.finditer(answer)}
    unknown_numbers = cited_numbers - source_numbers
    unknown_shas = {
        sha
        for sha in cited_shas
        if sha not in source_shas and not any(source_sha.startswith(sha) for source_sha in source_shas)
    }
    if unknown_numbers or unknown_shas:
        return GuardResult(
            False,
            "Answer cited references that were not present in the retrieved context: "
            f"numbers={sorted(unknown_numbers)}, shas={sorted(unknown_shas)}",
        )
    return GuardResult(True, "All cited references are present in retrieved context.")


class NLIGuard:
    def __init__(self) -> None:
        settings = get_settings()
        self.enabled = settings.enable_nli
        self.model = None
        self.tokenizer = None
        if self.enabled:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(settings.nli_model)
            self.model = AutoModelForSequenceClassification.from_pretrained(settings.nli_model)

    def check(self, answer: str, docs: list[Document]) -> GuardResult:
        citation_result = validate_citations(answer, docs)
        if not citation_result.passed:
            return citation_result
        if not self.enabled or self.model is None or self.tokenizer is None:
            return citation_result
        premise = "\n\n".join(doc.page_content[:1500] for doc in docs[:6])
        hypothesis = answer[:2000]
        if not premise.strip():
            return GuardResult(False, "No premise text available for support checking.")
        inputs = self.tokenizer(
            premise,
            hypothesis,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        )
        outputs = self.model(**inputs)
        entailment_id = self.model.config.label2id.get("ENTAILMENT", 2)
        contradiction_id = self.model.config.label2id.get("CONTRADICTION", 0)
        probs = outputs.logits.softmax(dim=-1)[0]
        if probs[contradiction_id].item() > probs[entailment_id].item():
            return GuardResult(False, "NLI guard judged the answer unsupported by retrieved sources.")
        return GuardResult(True, "Citations and NLI support check passed.")
