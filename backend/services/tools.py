"""Blueprint implementations for the LangGraph toolset."""
from __future__ import annotations

from typing import Any, Dict

from .process_tracker import ProcessTracker

tracker = ProcessTracker()


def tool_check_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Inspect production schedule entries and return a filtered view."""

    raise NotImplementedError("Populate with custom schedule inspection logic")


def check_stock(product: str) -> Dict[str, Any]:
    """Return inventory status for the requested product."""

    raise NotImplementedError("Implement local stock validation logic")


def machine_a(name: str, number: int) -> Dict[str, Any]:
    """Simulate running machine A. Updates tracker duration while active."""

    raise NotImplementedError("Wire machine A to process tracker and machine data store")


def machine_b(name: str, number: int) -> Dict[str, Any]:
    """Simulate running machine B. Updates tracker duration while active."""

    raise NotImplementedError("Wire machine B to process tracker and machine data store")


def machine_c(name: str, number: int) -> Dict[str, Any]:
    """Simulate running machine C. Updates tracker duration while active."""

<<<<<<< Updated upstream
    raise NotImplementedError("Wire machine C to process tracker and machine data store")
=======
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
>>>>>>> Stashed changes
