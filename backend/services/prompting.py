"""Prompt customization hooks for the factory agent."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .data_store import get_data_store
from .text_base import build_text_base, list_known_products

STORE = get_data_store()


def enrich_owner_prompt(message: str) -> str:
    """Inject timestamp, processing-time lookup, and resource summaries."""

    sections: List[str] = [message]
    current_time = datetime.utcnow().isoformat()
    sections.append(f"[timestamp]\n{current_time}")

    products = _detect_products(message)
    if products:
        processing_section = _build_processing_time_section(products)
        if processing_section:
            sections.append(processing_section)

        text_base = build_text_base(products)
        if text_base:
            sections.append(f"[text_base]\n{text_base}")

    return "\n\n".join(sections)


def build_completion_prompt(context: Dict[str, Any]) -> str:
    """Describe a machine completion event to the LLM."""

    machine = context.get("machine", "unknown machine").upper()
    order_id = context.get("order_id", "unknown order")
    product = context.get("product", "unknown product")
    finished_at = datetime.utcnow().isoformat()
    schedule = context.get("schedule", [])
    schedule_text = context.get("schedule_text") or schedule

    base_prompt = (
        "Machine {machine} finished order {order_id} for product {product} at {time}.\n"
        "Report the completed work, then examine the current schedule JSON below.\n"
        "If there are pending orders, choose the best candidate and call the appropriate "
        "tool to continue production.\n\nSchedule:\n{schedule}\n"
    ).format(
        machine=machine,
        order_id=order_id,
        product=product,
        time=finished_at,
        schedule=schedule_text,
    )
    if not schedule:
        base_prompt += "No pending orders remain. Confirm the factory is idle."
    else:
        base_prompt += "After selecting the next job, explain why you chose it."
    return base_prompt


def _detect_products(message: str) -> List[str]:
    catalog = list_known_products()
    lowered = message.lower()
    matches = []
    for product in catalog:
        if product.lower() in lowered:
            matches.append(product)
    return matches


def _build_processing_time_section(products: List[str]) -> str:
    processing_times = STORE.load_processing_times()
    lines: List[str] = []
    for product in products:
        if product in processing_times:
            lines.append(f"{product}: {processing_times[product]} seconds per unit")
    if not lines:
        return ""
    return "[processing_time_lookup]\n" + "\n".join(lines)
