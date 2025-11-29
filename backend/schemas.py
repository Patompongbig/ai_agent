"""Pydantic schemas shared by FastAPI routers and LangGraph."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ScheduleEntry(BaseModel):
    order_id: str
    product: str
    quantity: int
    order_time: datetime
    process_time_sec: int
    deadline: datetime


class QueryRequest(BaseModel):
    message: str = Field(..., description="Free-form question from the factory owner")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional UI context")


class QueryResponse(BaseModel):
    plan: Dict[str, Any]
    raw_messages: Dict[str, Any]


class InventorySnapshot(BaseModel):
    materials_available: Dict[str, float]
    materials_usage: Dict[str, Dict[str, float]]


class MachineState(BaseModel):
    states: Dict[str, int]
    durations: Dict[str, float]
