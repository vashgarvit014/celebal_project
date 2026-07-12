from __future__ import annotations

import argparse

from patchcontext.answer import answer_question


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask PatchContext a question.")
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=8)
    args = parser.parse_args()
    result = answer_question(args.question, k=args.k)
    print(result.answer)
    print("\nSources:")
    for source in result.sources:
        print(f"- {source.label}: {source.title} ({source.url})")


if __name__ == "__main__":
    main()

