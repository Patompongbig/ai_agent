"""Prompt customization hooks for the factory agent."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


def enrich_owner_prompt(message: str) -> str:
    """Allow users to tweak the owner's message before it hits the LLM."""

    return message


def build_completion_prompt(context: Dict[str, Any]) -> str:
    """Describe a machine completion event to the LLM."""

    machine = context.get("machine", "unknown machine").upper()
    order_id = context.get("order_id", "unknown order")
    product = context.get("product", "unknown product")
    finished_at = datetime.utcnow().isoformat()
    schedule = context.get("schedule", [])

    return (
        "Machine {machine} finished order {order_id} for product {product} at {time}.\n"
        "Here is the current schedule JSON:\n{schedule}\n"
        "Please decide what should happen next and explain your reasoning."
    ).format(machine=machine, order_id=order_id, product=product, time=finished_at, schedule=schedule)
