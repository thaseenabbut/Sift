import logging

from src.ai_overview.citations import get_citations
from src.ai_overview.context import ContextBuilder
from src.ai_overview.evaluator import evaluate_evidence
from src.ai_overview.llm import generate
from src.ai_overview.prompt import build_messages
from src.ai_overview.retriever import retrieve_chunks
from src.api.schemas import AIOverviewResponse
from storage.vectordb import VectorDB

logger = logging.getLogger(__name__)

class AIOverviewService:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.context_builder = ContextBuilder()

    async def retrieve(self, query: str) -> list[dict]:
        return await retrieve_chunks(
            query=query,
            vector_db=self.vector_db,
        )

    def build_context(self, retrieved_chunks: list[dict]) -> dict:
        return self.context_builder.build(retrieved_chunks)

    def get_sources(self, context: dict) -> list[dict]:
        return get_citations(context)

    def build_prompt(self, query: str, context: dict) -> list[dict]:
        return build_messages(query=query, context=context["context"])

    async def generate_from_messages(self, messages: list[dict]) -> str | None:
        return await generate(messages)

    async def generate_overview(self, query: str) -> AIOverviewResponse:
        clean_query = query.strip()
        if not clean_query:
            return AIOverviewResponse(
                status="NOT_GENERATED_DUE_TO_EMPTY_QUERY",
                reason="Query cannot be empty",
                overview=None, 
                sources=[]
            )

        try:
            chunks = await self.retrieve(clean_query)
        except Exception:
            logger.exception("AI Overview chunk retrieval failed")

            return AIOverviewResponse(
                status="NOT_GENERATED_DUE_TO_RETRIEVAL_ERROR",
                reason="Chunk retrieval failed",
                overview=None,
                sources=[],
            )

        context = self.build_context(chunks)
        sources = self.get_sources(context)

        evaluation = evaluate_evidence(
            query=clean_query,
            context=context,
            chunks=chunks,
        )
        if not evaluation["sufficient"]:
            return AIOverviewResponse(
                status="NOT_GENERATED_DUE_TO_INSUFFICIENT_EVIDENCE",
                reason=evaluation["reason"],
                overview=None,
                sources=sources,
            )

        messages = self.build_prompt(clean_query, context)
        overview = await self.generate_from_messages(messages)

        if not overview:
            return AIOverviewResponse(
                status="NOT_GENERATED_DUE_TO_LLM_ERROR",
                reason=evaluation["reason"],
                overview=None, 
                sources=[]
            )

        return AIOverviewResponse(
            status="GENERATED_SUCCESSFULLY",
            overview=overview,
            sources=sources,
        )
