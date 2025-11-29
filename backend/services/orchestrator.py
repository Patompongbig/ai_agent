<<<<<<< Updated upstream
<<<<<<< Updated upstream
"""High-level service that wires FastAPI endpoints to LangGraph."""
=======
"""Factory orchestrator using LangGraph's create_react_agent with Ollama."""
>>>>>>> Stashed changes
=======
"""Factory orchestrator using LangGraph's create_react_agent with Ollama."""
>>>>>>> Stashed changes
from __future__ import annotations

import logging
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
=======
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
>>>>>>> Stashed changes
=======
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
>>>>>>> Stashed changes

from ..config import settings
from ..schemas import QueryRequest
from .langgraph_factory import FactoryState, create_smart_factory_graph
from .tools import check_stock, machine_a, machine_b, machine_c, tool_check_schedule

logger = logging.getLogger(__name__)


class FactoryOrchestrator:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    """Facilitates conversations between the UI, tools, and LangGraph."""
=======
    """Coordinates FastAPI requests, tools, and the LangGraph agent."""
>>>>>>> Stashed changes
=======
    """Coordinates FastAPI requests, tools, and the LangGraph agent."""
>>>>>>> Stashed changes

    def __init__(self) -> None:
        self.tools = self._init_tools()
        self.llm = self._init_llm()
        self.graph = create_smart_factory_graph(self.llm, self.tools)

<<<<<<< Updated upstream
<<<<<<< Updated upstream
    def _init_llm(self) -> Runnable:
        """Return the ChatOpenAI client or a safe fallback when no key is configured."""

        if settings.openai_api_key:
            client_kwargs: Dict[str, Any] = {
                "model": settings.llm_model,
                "temperature": 0,
                "api_key": settings.openai_api_key,
            }
            if settings.openai_base_url:
                client_kwargs["base_url"] = settings.openai_base_url
            return ChatOpenAI(**client_kwargs)

        logger.warning(
            "OPENAI_API_KEY not set. Falling back to a mock LLM; /api/query responses "
            "will be placeholders until a real API key is provided."
        )
        return RunnableLambda(
            lambda messages: AIMessage(
                content="LLM unavailable: configure OPENAI_API_KEY to enable decisions."
            )
        )

    def _init_tools(self) -> list[Tool]:
        return [
            Tool.from_function(
                name="check_schedule",
                description="Inspect and reason about the production schedule JSON",
                func=tool_check_schedule,
            ),
            Tool.from_function(
                name="check_stock",
                description="Validate raw material inventory for a product",
                func=check_stock,
            ),
            Tool.from_function(
                name="machine_a",
                description="Reserve machine A for a production task",
                func=machine_a,
            ),
            Tool.from_function(
                name="machine_b",
                description="Reserve machine B for a production task",
                func=machine_b,
            ),
            Tool.from_function(
                name="machine_c",
                description="Reserve machine C for a production task",
                func=machine_c,
            ),
        ]

    async def run(self, payload: QueryRequest) -> Dict[str, Any]:
        state: FactoryState = {
            "messages": [],
            "context": {
                "query": payload.message,
                "metadata": payload.metadata or {},
            },
        }
        return await self.graph.ainvoke(state)
=======
=======
>>>>>>> Stashed changes
    def _init_llm(self) -> Optional[ChatOllama]:
        try:
            return ChatOllama(
                model=settings.llm_model,
                base_url=settings.ollama_base_url,
                temperature=0,
            )
        except Exception:  # pragma: no cover - defensive logging
            logger.exception(
                "Unable to initialize ChatOllama. Ensure Ollama is running at %s",
                settings.ollama_base_url,
            )
            return None

    def _build_prompt(self) -> str:
        return (
            """You are the factory manager of a shoe manufacturing plant. You have full autonomy to plan production, schedule work, inspect inventory, and decide when and how to use the available tools. Act like a real production line supervisor who understands constraints, prioritizes efficiency, and ensures customer requests are fulfilled correctly.

Available tools you may use:

add_order_to_schedule
Adds a new production order into schedule.json and automatically generates an order_id.
Example input:
{ "product": "shoe_a", "quantity": 10, "order_time": "2025-11-30T04:12:00", "process_time_sec": 50, "deadline": "2025-12-05" }

get_schedule
Loads and returns the full list of production orders from schedule.json.

load_materials_available
Loads and returns raw material inventory from materials_available.json.

resource_tool
Returns the material requirements per product, stock currently available, and which machines are free (status = 1). Used for check machine availability

assign_machine
Assigns a machine A B or C to start production for an existing order.
This tool validates material availability, deducts inventory, marks the machine as busy, removes the order from schedule.json, and starts a processing timer.
Example input:
{ "item_name": "shoe", "quantity": 20, "machine": "A", "order_id": "ORD-002" }

Your main objectives:

Understand the user’s intention, such as producing new items, checking stock, reviewing capacity, or managing the job queue.

Plan production efficiently considering raw materials, machine availability, deadlines, and existing scheduled orders.

Decide which tools to call based on what the user is trying to do. You do not need to use every tool every time.

Produce the best possible result with the information available.

General guidelines:

If the user asks to produce a new product:
You typically add a new order using add_order_to_schedule.
You may optionally check materials or machines using load_materials_available or resource_tool.
If everything is ready, you may immediately call assign_machine to start production.

If the user asks for status or an overview:
Use get_schedule, resource_tool, or load_materials_available as appropriate.

Required response format:

First summarize what you understood and what actions you performed along with the final result.
Then list the tools you used in this response. For example:
Tools Used:
add_order_to_schedule used to create a new order with order_id ORD-004
assign_machine used to assign Machine A to produce 10 units of shoe_a

If no tools were used, write:
No tools used this time. Reason: (explain briefly)

Special notes:

Internal machine names are machine_a machine_b and machine_c.
When speaking to the user, refer to them as Machine A Machine B and Machine C.

Metadata may be attached to a user command. For example, a user might say
Produce 10 units of widget_a
and metadata may include timestamp processing_time_lookup or text_base.
Use metadata when available to determine the current time or processing times.
If metadata is missing, you may fall back to tools such as resource_tool.

Failure handling:

If an action cannot be completed due to insufficient materials, no available machines, missing order_id, or other issues, explain clearly why it cannot be done and suggest alternative actions such as rescheduling, partial production, or replenishing materials."""
        )

    def _init_agent(self):
        if not self.llm:
            return None
        return create_react_agent(
            self.llm,
            TOOLKIT,
            prompt=self.prompt,
            debug=True,
        )

    async def run(self, payload: QueryRequest) -> Dict[str, Any]:
        if not self.agent:
            return {
                "output": "Ollama unavailable. Start Ollama locally and retry.",
                "intermediate_steps": [],
            }

        enriched = enrich_owner_prompt(payload.message)
        agent_input = self._format_input(enriched, payload.metadata)
        result = await self.agent.ainvoke({"messages": [HumanMessage(content=agent_input)]})
        output, trace = self._extract_output(result)
        serialized_trace = [self._serialize_message(message) for message in trace]
        return {"output": output, "intermediate_steps": serialized_trace}

    def _format_input(self, message: str, metadata: Optional[Dict[str, Any]]) -> str:
        if not metadata:
            return message
        serialized = json.dumps(metadata, ensure_ascii=False)
        return f"{message}\n\n[metadata]\n{serialized}"

    def _extract_output(self, result: Dict[str, Any]) -> tuple[str, List[Any]]:
        messages: List[Any] = result.get("messages", [])
        final_text = ""
        for message in reversed(messages):
            if getattr(message, "type", "") == "ai":
                final_text = getattr(message, "content", "")
                break
        return final_text, messages

    def _serialize_message(self, message: Any) -> Dict[str, Any]:
        """Convert LangChain message objects into JSON-friendly logs."""

        def _stringify_content(content: Any) -> str:
            if content is None:
                return ""
            if isinstance(content, str):
                return content
            try:
                return json.dumps(content, ensure_ascii=False)
            except TypeError:
                return str(content)

        entry: Dict[str, Any] = {
            "type": getattr(message, "type", ""),
            "content": _stringify_content(getattr(message, "content", "")),
        }
        name = getattr(message, "name", None) or getattr(message, "tool", None)
        if name:
            entry["name"] = name
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            entry["tool_calls"] = tool_calls
        tool_input = getattr(message, "input", None)
        if tool_input is not None:
            entry["tool_input"] = tool_input
        return entry

    async def _handle_machine_completion(self, context: Dict[str, Any]) -> None:
        if not self.agent:
            logger.info("Skipping completion callback because Ollama is unavailable")
            return
        prompt = build_completion_prompt(context)
        try:
            result = await self.agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
            output, _ = self._extract_output(result)
            logger.info(
                "Auto-run after %s completion -> %s",
                context.get("machine"),
                output,
            )
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Auto-run agent invocation failed after completion")
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes


def orchestrator_factory() -> FactoryOrchestrator:
    return FactoryOrchestrator()


orchestrator = orchestrator_factory()
