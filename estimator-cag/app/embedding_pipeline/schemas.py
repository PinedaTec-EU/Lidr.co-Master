from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChunkingStrategy(str, Enum):
    STRUCTURAL = "structural"
    FIXED_WINDOW = "fixed_window"
    HIERARCHICAL = "hierarchical"


class EmbeddingModelName(str, Enum):
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"


class ClientMetadata(BaseModel):
    name: str = Field(min_length=1)
    sector: str = Field(min_length=1)
    country: str = Field(min_length=2, max_length=2)


class BudgetComponent(BaseModel):
    component_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tech_stack: list[str] = Field(default_factory=list)
    complexity: ComplexityLevel
    estimated_hours: int = Field(ge=0)
    dependencies: list[str] = Field(default_factory=list)


class Budget(BaseModel):
    budget_id: str = Field(min_length=1)
    client_metadata: ClientMetadata
    project_summary: str = Field(min_length=1)
    main_technology: str = Field(min_length=1)
    year: int = Field(ge=2000, le=2100)
    total_estimated_hours: int = Field(ge=0)
    components: list[BudgetComponent] = Field(min_length=1)


class ChunkMetadata(BaseModel):
    budget_id: str
    component_id: str
    client_sector: str
    main_technology: str
    year: int
    complexity: ComplexityLevel
    estimated_hours: int


class Chunk(BaseModel):
    chunk_id: str
    text: str
    metadata: ChunkMetadata
    token_count: int = Field(ge=0)
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.STRUCTURAL
    llm_context: str | None = None


class EmbeddedChunk(Chunk):
    embedding: list[float] = Field(min_length=1)
    embedding_model: EmbeddingModelName = EmbeddingModelName.TEXT_EMBEDDING_3_SMALL


class ChunkingOptions(BaseModel):
    strategy: ChunkingStrategy = ChunkingStrategy.STRUCTURAL
    include_parent_context: bool = True
    max_characters: int = Field(default=900, ge=200, le=6000)
    overlap_characters: int = Field(default=120, ge=0, le=1000)
    llm_enrich_context: bool = False


class DocumentIngestRequest(BaseModel):
    source_path: str = Field(min_length=1)
    document_type: str = Field(min_length=1, max_length=50)
    content: Budget
    chunking: ChunkingOptions = Field(default_factory=ChunkingOptions)
    embedding_model: EmbeddingModelName = EmbeddingModelName.TEXT_EMBEDDING_3_SMALL


class DocumentIngestResponse(BaseModel):
    document_id: int = Field(ge=1)
    chunks_created: int = Field(ge=0)
    embedding_dimension: int = Field(ge=1)
    ingestion_time_ms: float = Field(ge=0)


class SearchFilters(BaseModel):
    client_sector: str | None = None
    main_technology: str | None = None
    year: int | None = None
    complexity: ComplexityLevel | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=50)
    embedding_model: EmbeddingModelName = EmbeddingModelName.TEXT_EMBEDDING_3_SMALL
    filters: SearchFilters | None = None


class SearchMatch(BaseModel):
    chunk_id: str
    text: str
    metadata: ChunkMetadata
    token_count: int = Field(ge=0)
    chunking_strategy: ChunkingStrategy
    embedding_model: EmbeddingModelName
    score: float
    llm_context: str | None = None


class SearchStats(BaseModel):
    returned_matches: int = Field(ge=0)
    latency_ms: float = Field(ge=0)


class SearchResponse(BaseModel):
    matches: list[SearchMatch]
    stats: SearchStats


class RetrievalEvalCase(BaseModel):
    query: str = Field(min_length=3)
    relevant_chunk_ids: list[str] = Field(min_length=1)
    filters: SearchFilters | None = None


class RetrievalEvalRequest(BaseModel):
    cases: list[RetrievalEvalCase] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    embedding_model: EmbeddingModelName = EmbeddingModelName.TEXT_EMBEDDING_3_SMALL


class RetrievalEvalCaseResult(BaseModel):
    query: str
    relevant_chunk_ids: list[str]
    retrieved_chunk_ids: list[str]
    recall_at_k: float
    ndcg_at_k: float


class RetrievalEvalSummary(BaseModel):
    mean_recall_at_k: float
    mean_ndcg_at_k: float


class RetrievalEvalResponse(BaseModel):
    cases: list[RetrievalEvalCaseResult]
    summary: RetrievalEvalSummary
