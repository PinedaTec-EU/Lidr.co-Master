from enum import Enum

from pydantic import BaseModel, Field

from app.embedding_pipeline.schemas import QueryRewriteStrategy


class ProjectType(str, Enum):
    MOBILE_APP = "mobile_app"
    WEB_SAAS = "web_saas"
    INTERNAL_TOOL = "internal_tool"
    DATA_PIPELINE = "data_pipeline"


class DetailLevel(str, Enum):
    SUMMARY = "summary"
    MEDIUM = "medium"
    DETAILED = "detailed"


class OutputFormat(str, Enum):
    PHASES_TABLE = "phases_table"
    LINE_ITEMS = "line_items"
    NARRATIVE = "narrative"


class UserTier(str, Enum):
    DEVELOPER = "developer"
    PM = "pm"
    EXECUTIVE = "executive"


class RetrievalContextConfig(BaseModel):
    enabled: bool = False
    query_override: str | None = Field(default=None, min_length=3, max_length=2000)
    k: int = Field(default=5, ge=1, le=50)
    score_threshold: float | None = Field(default=None, ge=0, le=1)
    rewrite_strategy: QueryRewriteStrategy = QueryRewriteStrategy.DISABLED
    max_chunks: int = Field(default=3, ge=1, le=12)
    max_context_chars: int = Field(default=1800, ge=400, le=12000)
    include_scores: bool = True


class RetrievalPromptContext(BaseModel):
    query: str
    effective_query: str
    context_text: str
    included_chunks_count: int = Field(ge=0)
    retrieved_results_count: int = Field(ge=0)
    truncated: bool = False


class EstimationRequest(BaseModel):
    description: str = Field(min_length=20, max_length=2000)
    project_type: ProjectType
    detail_level: DetailLevel
    output_format: OutputFormat
    retrieval: RetrievalContextConfig = Field(default_factory=RetrievalContextConfig)


class EstimationResponse(BaseModel):
    text: str
    prompt_version: str


class TranscriptEstimateRequest(BaseModel):
    transcript: str = Field(min_length=100, max_length=50000)
    idempotency_key: str | None = Field(default=None, max_length=128)
    project_type: ProjectType = ProjectType.WEB_SAAS
    detail_level: DetailLevel = DetailLevel.MEDIUM
    output_format: OutputFormat = OutputFormat.NARRATIVE
    retrieval: RetrievalContextConfig = Field(default_factory=RetrievalContextConfig)


class TranscriptEstimateResponse(EstimationResponse):
    model: str
    provider: str
    tokens_used: dict
    latency_ms: float
    cost_usd: float
    request_id: str
    idempotency_cache_hit: bool = False
    retrieval_context_included: bool = False
    retrieved_results_count: int = Field(default=0, ge=0)
    included_chunks_count: int = Field(default=0, ge=0)


class SessionCreateResponse(BaseModel):
    session_id: str


class SessionDetailResponse(BaseModel):
    session_id: str
    user_tier: UserTier | None = None
    user_display_name: str | None = None
    turns: list[tuple[str, str]]
    message_count: int
    anchors_count: int
    summary_chars: int
    last_resolved_tier: UserTier | None = None
    last_tier_rule: str | None = None
    project_metadata: dict
    external_context_config: dict
    document_sources: list[str]
    conversation_messages: list[dict[str, str]]
    last_document_context: list[str]
    last_external_context: list[dict]
    last_run_info: dict
    turn_observations: list[dict]
    last_turn_observed: dict | None = None
