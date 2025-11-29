"""LangChain tool definitions for the smart factory."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain.tools import tool
from pydantic import BaseModel, Field

from .data_store import JSONDataStore, get_data_store
from .runtime import runtime_manager

STORE: JSONDataStore = get_data_store()


class AddOrderInput(BaseModel):
    product: str
    quantity: int = Field(gt=0)
    order_time: str
    process_time_sec: int = Field(gt=0)
    deadline: str


class ResourceToolInput(BaseModel):
    product_names: List[str] = Field(
        ..., description="List of product names to inspect"
    )


class AssignMachineInput(BaseModel):
    item_name: str = Field(..., description="Product to produce")
    quantity: int = Field(gt=0)
    machine: str = Field(..., description="Machine identifier (A/B/C or machine_a)")
    order_id: str


@tool("add_order_to_schedule", args_schema=AddOrderInput)
def add_order_to_schedule(
    product: str,
    quantity: int,
    order_time: str,
    process_time_sec: int,
    deadline: str,
) -> Dict[str, Any]:
    """Append an order to schedule.json and return the new schedule."""

    schedule = STORE.load_schedule()
    order_id = _next_order_id(schedule)
    new_order = {
        "order_id": order_id,
        "product": product,
        "quantity": quantity,
        "order_time": order_time,
        "process_time_sec": process_time_sec,
        "deadline": deadline,
    }
    schedule.append(new_order)
    STORE.save_schedule(schedule)
    return {"schedule": schedule, "order": new_order}


@tool("get_schedule")
def get_schedule() -> Dict[str, Any]:
    """Return the entire production schedule."""

    return {"schedule": STORE.load_schedule()}


@tool("load_materials_available")
def load_materials_available() -> Dict[str, Any]:
    """Return the materials_available.json payload."""

    return {"materials_available": STORE.load_materials_available()}


@tool("resource_tool", args_schema=ResourceToolInput)
def resource_tool(product_names: List[str]) -> Dict[str, Any]:
    """Return available machines and material requirements for requested products."""

    machines = STORE.load_machine_states()
    materials_usage = STORE.load_materials_usage()
    inventory = STORE.load_materials_available()

    available_machines = {name: status for name, status in machines.items() if status == 1}
    products: List[Dict[str, Any]] = []

    for product in product_names:
        usage = materials_usage.get(product)
        if not usage:
            products.append(
                {
                    "product_name": product,
                    "error": "Product not configured in materials_usage.json",
                }
            )
            continue

        materials_needed = [
            {
                "material_name": material,
                "quantity_per_unit": amount,
                "stock_remaining": inventory.get(material, 0),
            }
            for material, amount in usage.items()
        ]
        products.append({"product_name": product, "materials_needed": materials_needed})

    return {"machines_status": available_machines, "products": products}


@tool("assign_machine", args_schema=AssignMachineInput)
def assign_machine(
    item_name: str,
    quantity: int,
    machine: str,
    order_id: str,
) -> Dict[str, Any]:
    """Assign a machine to an order, deduct inventory, and start a countdown."""

    try:
        normalized_machine = _normalize_machine(machine)
    except ValueError as exc:
        return {
            "success": False,
            "message": str(exc),
        }
    machines = STORE.load_machine_states()
    if normalized_machine not in machines:
        return {
            "success": False,
            "message": f"Unknown machine '{machine}'.",
        }
    if machines[normalized_machine] == 0:
        return {
            "success": False,
            "message": f"Machine {machine} is busy.",
        }

    processing_times = STORE.load_processing_times()
    if item_name not in processing_times:
        return {
            "success": False,
            "message": f"No processing time found for {item_name}.",
        }

    materials_usage = STORE.load_materials_usage()
    if item_name not in materials_usage:
        return {
            "success": False,
            "message": f"No materials usage configured for {item_name}.",
        }

    inventory = STORE.load_materials_available()
    missing: List[str] = []
    for material, per_unit in materials_usage[item_name].items():
        required = per_unit * quantity
        if inventory.get(material, 0) < required:
            missing.append(
                f"{material} (required {required}, available {inventory.get(material, 0)})"
            )
    if missing:
        return {
            "success": False,
            "message": f"Insufficient materials: {', '.join(missing)}",
        }

    for material, per_unit in materials_usage[item_name].items():
        required = per_unit * quantity
        inventory[material] = inventory.get(material, 0) - required
    STORE.save_materials_available(inventory)

    schedule = STORE.load_schedule()
    schedule = [entry for entry in schedule if entry.get("order_id") != order_id]
    STORE.save_schedule(schedule)

    duration_seconds = max(1, int(processing_times[item_name] * quantity))
    runtime_manager.start_job(
        normalized_machine,
        duration_seconds,
        {
            "order_id": order_id,
            "product": item_name,
            "quantity": quantity,
            "schedule": schedule,
        },
    )

    return {
        "success": True,
        "message": (
            f"Assigned {normalized_machine} to order {order_id}. Duration {duration_seconds} seconds."
        ),
        "machine": normalized_machine,
        "duration_seconds": duration_seconds,
        "inventory": inventory,
        "schedule": schedule,
    }


def _next_order_id(schedule: List[Dict[str, Any]]) -> str:
    if not schedule:
        return "ORD-001"
    last = schedule[-1]["order_id"]
    try:
        prefix, number = last.split("-")
        next_number = int(number) + 1
        return f"{prefix}-{next_number:03d}"
    except Exception:
        return "ORD-001"


def _normalize_machine(machine: str) -> str:
    token = machine.strip().lower()
    if token in {"a", "b", "c"}:
        return f"machine_{token}"
    if token.startswith("machine_"):
        return token
    raise ValueError(f"Unsupported machine identifier: {machine}")
