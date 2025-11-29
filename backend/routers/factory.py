"""FastAPI router exposing smart factory endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas import (
    InventorySnapshot,
    MachineState,
    QueryRequest,
    QueryResponse,
    ScheduleEntry,
)
from ..services.data_store import JSONDataStore, get_data_store
from ..services.orchestrator import orchestrator
from ..services.runtime import runtime_manager

router = APIRouter(prefix="/api", tags=["factory"])


@router.get("/schedule", response_model=list[ScheduleEntry])
def list_schedule(store: JSONDataStore = Depends(get_data_store)):
    """Return every order currently planned for the factory."""

    entries = store.load_schedule()
    return [ScheduleEntry(**entry) for entry in entries]


@router.get("/inventory", response_model=InventorySnapshot)
def get_inventory(store: JSONDataStore = Depends(get_data_store)):
    """Expose local view of materials usage and availability."""

    materials_available = store.load_materials_available()
    materials_usage = store.load_materials_usage()
    return InventorySnapshot(
        materials_available=materials_available,
        materials_usage=materials_usage,
    )


@router.get("/machines", response_model=MachineState)
def get_machine_state(store: JSONDataStore = Depends(get_data_store)):
    """Show current machine toggles and accumulated runtime."""

    states = store.load_machine_states()
    durations = runtime_manager.summarize()
    return MachineState(states=states, durations=durations)


@router.post("/query", response_model=QueryResponse)
async def run_owner_query(payload: QueryRequest):
    """Send a natural-language query into the ReAct agent orchestrator."""

    raw_response = await orchestrator.run(payload)
    return QueryResponse(**raw_response)
