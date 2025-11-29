"""Helpers for building per-product resource summaries."""
from __future__ import annotations

from typing import Dict, Iterable, List

from .data_store import JSONDataStore, get_data_store

store: JSONDataStore = get_data_store()


def list_known_products() -> List[str]:
    return list(store.load_materials_usage().keys())


def build_product_summary(product: str) -> str:
    materials_usage = store.load_materials_usage().get(product)
    processing_time = store.load_processing_times().get(product)

    lines: List[str] = [f"Product: {product}"]
    if processing_time is not None:
        lines.append(f"- Process time per unit: {processing_time} seconds")
    if materials_usage:
        lines.append("- Materials per unit:")
        for material, qty in materials_usage.items():
            lines.append(f"  • {material}: {qty}")
    return "\n".join(lines)


def build_text_base(products: Iterable[str]) -> str:
    summaries = [build_product_summary(product) for product in products]
    return "\n\n".join(summary for summary in summaries if summary)
