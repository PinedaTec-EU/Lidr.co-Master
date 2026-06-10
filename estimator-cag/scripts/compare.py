from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.schemas import EmbeddingModelName


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b, strict=True))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("Cosine similarity is undefined for zero-length vectors.")
    return dot_product / (norm_a * norm_b)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two texts with OpenAI embeddings.")
    parser.add_argument("--text-a", required=True)
    parser.add_argument("--text-b", required=True)
    parser.add_argument(
        "--model",
        default=EmbeddingModelName.TEXT_EMBEDDING_3_SMALL.value,
        choices=[model.value for model in EmbeddingModelName],
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    try:
        embedder = OpenAIEmbedder(model_name=EmbeddingModelName(args.model))
        embedding_a = embedder.embed_one(args.text_a)
        embedding_b = embedder.embed_one(args.text_b)
        similarity = cosine_similarity(embedding_a, embedding_b)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Text A: {args.text_a}")
    print(f"Text B: {args.text_b}")
    print(f"Model: {args.model}")
    print(f"Cosine similarity: {similarity:.4f}")


if __name__ == "__main__":
    main()
