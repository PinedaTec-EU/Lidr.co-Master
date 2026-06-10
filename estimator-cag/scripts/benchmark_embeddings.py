from __future__ import annotations

from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.schemas import EmbeddingModelName
from scripts.compare import cosine_similarity

PAIRS = [
    (
        "close-auth",
        "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app",
        "Authorization service using JSON Web Tokens for a banking application",
    ),
    (
        "far-auth-vs-migration",
        "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app",
        "Database migration from MySQL to PostgreSQL with zero downtime",
    ),
    (
        "generic-backend",
        "Backend services",
        "API development",
    ),
]


def main() -> None:
    load_dotenv()
    for model in EmbeddingModelName:
        embedder = OpenAIEmbedder(model_name=model)
        print(f"## {model.value}")
        for label, text_a, text_b in PAIRS:
            embedding_a = embedder.embed_one(text_a)
            embedding_b = embedder.embed_one(text_b)
            similarity = cosine_similarity(embedding_a, embedding_b)
            print(f"{label}: {similarity:.4f}")
        print("")


if __name__ == "__main__":
    main()
