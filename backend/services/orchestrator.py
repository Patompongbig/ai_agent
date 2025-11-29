"""Factory orchestrator built on LangChain's ReAct agent."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from langchain.agents import create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from ..config import settings
from ..schemas import QueryRequest
from .prompting import build_completion_prompt, enrich_owner_prompt
from .runtime import runtime_manager
from .tools import (
    add_order_to_schedule,
    assign_machine,
    get_schedule,
    load_materials_available,
    resource_tool,
)

logger = logging.getLogger(__name__)

TOOLKIT = [
    add_order_to_schedule,
    get_schedule,
    load_materials_available,
    resource_tool,
    assign_machine,
]


class FactoryOrchestrator:
    """Coordinates FastAPI requests, tools, and the LangChain agent."""

    def __init__(self) -> None:
        self.llm = self._init_llm()
        self.prompt = self._build_prompt()
        self.agent = self._init_agent()
        runtime_manager.register_completion_callback(self._handle_machine_completion)

    def _init_llm(self) -> Optional[ChatOpenAI]:
        if not settings.openai_api_key:
            logger.warning(
                "OPENAI_API_KEY not configured; /api/query will return placeholders."
            )
            return None
        client_kwargs: Dict[str, Any] = {
            "model": settings.llm_model,
            "temperature": 0,
            "api_key": settings.openai_api_key,
        }
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        return ChatOpenAI(**client_kwargs)

    def _build_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are the orchestration brain for {factory_name}. "
                        "Use the provided tools to reason over schedule.json and other "
                        "plant data. Be explicit about what you can or cannot do."
                    ).format(factory_name=settings.factory_name),
                ),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def _init_agent(self):
        if not self.llm:
            return None
        return create_react_agent(self.llm, TOOLKIT, prompt=self.prompt)

    async def run(self, payload: QueryRequest) -> Dict[str, Any]:
        if not self.agent:
            return {
                "output": "LLM unavailable. Set OPENAI_API_KEY to enable ReAct agent.",
                "intermediate_steps": [],
            }

        enriched = enrich_owner_prompt(payload.message)
        agent_input = self._format_input(enriched, payload.metadata)
        result = await self.agent.ainvoke({"input": agent_input})
        return {
            "output": result.get("output"),
            "intermediate_steps": result.get("intermediate_steps", []),
        }

    def _format_input(self, message: str, metadata: Optional[Dict[str, Any]]) -> str:
        if not metadata:
            return message
        serialized = json.dumps(metadata, ensure_ascii=False)
        return f"{message}\n\n[metadata]\n{serialized}"

    async def _handle_machine_completion(self, context: Dict[str, Any]) -> None:
        if not self.agent:
            logger.info("Skipping completion callback because LLM is unavailable")
            return
        prompt = build_completion_prompt(context)
        await self.agent.ainvoke({"input": prompt})


orchestrator = FactoryOrchestrator()
