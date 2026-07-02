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


class QueryRewriteStrategy(str, Enum):
    DISABLED = "disabled"
    NORMALIZE = "normalize"
    EXPAND = "expand"
    DECOMPOSE = "decompose"


class QueryFusionStrategy(str, Enum):
    CONSENSUS = "consensus"
    COVERAGE = "coverage"


class SearchStrategy(str, Enum):
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchTarget(str, Enum):
    BUDGETS = "budgets"
    TRANSCRIPTS = "transcripts"
    TECHNICAL_DOCS = "technical_docs"


class RerankStrategy(str, Enum):
    DISABLED = "disabled"
    TOKEN_OVERLAP = "token_overlap"


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
    document_type: str | None = None
    chunk_type: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=3)
    k: int = Field(default=5, ge=1, le=50)
    candidate_pool_k: int | None = Field(default=None, ge=1, le=100)
    score_threshold: float | None = Field(default=None, ge=0, le=1)
    rewrite_strategy: QueryRewriteStrategy = QueryRewriteStrategy.DISABLED
    max_rewrite_queries: int = Field(default=4, ge=1, le=4)
    search_strategy: SearchStrategy = SearchStrategy.SEMANTIC
    target_collections: list[SearchTarget] | None = None
    rrf_smoothing_k: int = Field(default=60, ge=1, le=200)
    rerank_strategy: RerankStrategy = RerankStrategy.DISABLED
    rerank_alpha: float = Field(default=0.7, ge=0, le=1)
    embedding_model: EmbeddingModelName = EmbeddingModelName.TEXT_EMBEDDING_3_SMALL
    filters: SearchFilters | None = None


class SearchResult(BaseModel):
    chunk_id: int = Field(ge=1)
    document_id: int = Field(ge=1)
    chunk_type: str
    content: str
    distance: float = Field(ge=0)
    score: float = Field(ge=0, le=1)
    semantic_score: float = Field(default=0, ge=0, le=1)
    lexical_score: float | None = Field(default=None, ge=0)
    fusion_score: float | None = Field(default=None, ge=0, le=1)
    rerank_score: float | None = Field(default=None, ge=0, le=1)
    metadata: dict


class SearchResponse(BaseModel):
    query: str
    effective_query: str
    effective_queries: list[str] = Field(default_factory=list)
    k: int = Field(ge=1)
    candidate_pool_k: int = Field(default=0, ge=0)
    score_threshold: float | None = Field(default=None, ge=0, le=1)
    rewrite_strategy: QueryRewriteStrategy = QueryRewriteStrategy.DISABLED
    query_fusion_strategy: QueryFusionStrategy | None = None
    search_strategy: SearchStrategy = SearchStrategy.SEMANTIC
    resolved_target_collections: list[SearchTarget] = Field(default_factory=list)
    routing_reason: str = ""
    rerank_strategy: RerankStrategy = RerankStrategy.DISABLED
    rrf_smoothing_k: int | None = Field(default=None, ge=1, le=200)
    rewrite_notes: list[str] = Field(default_factory=list)
    search_time_ms: float = Field(ge=0)
    low_confidence: bool = False
    total_candidates_considered: int = Field(default=0, ge=0)
    results: list[SearchResult]


class ContextAssemblyRequest(SearchRequest):
    max_context_chars: int = Field(default=2400, ge=400, le=12000)
    max_chunks: int = Field(default=4, ge=1, le=12)
    include_scores: bool = True


class ContextAssemblyItem(BaseModel):
    chunk_id: int = Field(ge=1)
    document_id: int = Field(ge=1)
    chunk_type: str
    score: float = Field(ge=0, le=1)
    metadata: dict
    excerpt: str


class ContextAssemblyResponse(BaseModel):
    search: SearchResponse
    context_text: str
    included_chunks: list[ContextAssemblyItem]
    truncated: bool = False


class RetrievalEvalCase(BaseModel):
    query: str = Field(min_length=3)
    relevant_chunk_ids: list[str] = Field(min_length=1)


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
