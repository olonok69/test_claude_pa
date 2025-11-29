import argparse
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .arc.models import ModelSettings, create_chat_model


def build_enrichment_prompt(base_report: str) -> str:
    return (
        "You are a senior analytics writer tasked with enriching a pre-show report.\n\n"
        "The text below is a data-correct base report that MUST be treated as ground truth. "
        "Your job is to rewrite it in a more polished, executive-friendly style, similar to a "
        "Claude Desktop report, while strictly preserving all numerical values, table structures, "
        "and factual statements. Do not change any numbers, dates, percentages, or counts.\n\n"
        "Keep the overall section structure, but you may:\n"
        "- Improve headings and subheadings for clarity.\n"
        "- Tighten wording and remove repetition.\n"
        "- Add short connective narrative where helpful.\n"
        "- Emphasize key strengths, risks, and business implications more clearly.\n\n"
        "Do NOT introduce new metrics or speculative content.\n\n"
        "Return a single Markdown document as your answer, with the same high-level sections "
        "as the input report.\n\n"
        "--- BASE REPORT START ---\n" + base_report + "\n--- BASE REPORT END ---\n"
    )


def enrich_report(
    input_path: Path,
    output_path: Path,
    provider: str,
    model_name: str,
    temperature: float,
    max_tokens: Optional[int] = None,
) -> None:
    base_text = input_path.read_text(encoding="utf-8")

    configured_max_tokens = max_tokens if max_tokens is not None else 8000

    settings = ModelSettings(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        max_tokens=configured_max_tokens,
    )
    model = create_chat_model(settings)

    prompt = build_enrichment_prompt(base_text)
    response = model.invoke(prompt)

    # LangChain-style models may return different types; normalize to string
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(str(part["text"]))
                else:
                    text_parts.append(str(part))
            content = "\n".join(text_parts)
    else:
        content = str(response)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(str(content), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich a pre-show report using an LLM.")
    parser.add_argument("--input", required=True, help="Path to base report markdown file")
    parser.add_argument("--output", required=True, help="Path to write enriched report markdown file")
    parser.add_argument("--provider", default="anthropic", help="LLM provider (e.g., anthropic, azure, openai)")
    parser.add_argument("--model", required=True, help="Model name to use for enrichment")
    parser.add_argument("--temperature", type=float, default=0.1, help="Sampling temperature (default 0.1)")
    parser.add_argument("--max-tokens", type=int, help="Optional max token override for the enrichment model")

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    load_dotenv()  # Load environment variables from .env file if present
    enrich_report(
        input_path,
        output_path,
        provider=args.provider,
        model_name=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )


if __name__ == "__main__":
    main()
