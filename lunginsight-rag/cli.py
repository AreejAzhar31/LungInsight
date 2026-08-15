"""
Minimal REPL for manually exercising LungInsightRAGService end-to-end.

    export GROQ_API_KEY=...           # required for real LLM calls
    python cli.py

Type `exit` to quit, `reset` to clear conversation memory. You can also seed
a fake prediction context once per session with:

    /predict suspicious_nodule 0.78 "right upper lobe"
"""
from __future__ import annotations

import sys

from service import LungInsightRAGService


def main() -> None:
    print("Building / loading knowledge base index...")
    rag = LungInsightRAGService()
    rag.ensure_index_built()
    print(f"Ready. Vector store backend: {rag.vector_store.backend_name}, chunks: {len(rag.vector_store)}\n")

    session_id = "cli-session"
    print("LungInsight AI (type 'exit' to quit, 'reset' to clear memory)\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not message:
            continue
        if message.lower() in {"exit", "quit"}:
            break
        if message.lower() == "reset":
            rag.reset_session(session_id)
            print("(conversation memory cleared)\n")
            continue

        prediction_context = None
        if message.startswith("/predict"):
            parts = message.split(maxsplit=3)
            if len(parts) >= 3:
                prediction_context = {
                    "predicted_class": parts[1],
                    "confidence": float(parts[2]),
                    "gradcam_region": parts[3].strip('"') if len(parts) > 3 else "unspecified",
                }
                print(f"(prediction context set: {prediction_context})\n")
                continue

        result = rag.chat(session_id, message, prediction_context=prediction_context)
        answer = result["answer"]

        if answer.get("refused"):
            print(f"\nLungInsight AI: {answer['plain_language_explanation']}\n")
            continue

        print("\n--- Plain-language explanation ---")
        print(answer["plain_language_explanation"])
        print("\n--- Clinical explanation ---")
        print(answer["clinical_explanation"])
        print("\n--- Recommended next steps ---")
        print(answer["recommended_next_steps"])
        print("\n--- Sources ---")
        print(answer["sources"])
        print("\n--- Confidence & disclaimer ---")
        print(answer["confidence_disclaimer"])
        print()


if __name__ == "__main__":
    sys.exit(main())
