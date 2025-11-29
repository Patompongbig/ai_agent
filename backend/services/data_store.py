"""Utility helpers for loading and updating local JSON data files."""
from __future__ import annotations

import json
from json import JSONDecodeError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ..config import settings


@dataclass
class JSONDataStore:
    """Simple JSON-backed persistence with in-memory caching."""

    schedule_path: Path = settings.data_paths.schedule
    processing_time_path: Path = settings.data_paths.processing_time
    materials_usage_path: Path = settings.data_paths.materials_usage
    materials_available_path: Path = settings.data_paths.materials_available
    machines_path: Path = settings.data_paths.machines

    def _read(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, path: Path, payload: Any) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _safe_read(self, path: Path, default: Any) -> Any:
        try:
            data = self._read(path)
        except (JSONDecodeError, FileNotFoundError):
            return default
        return default if data is None else data

    def load_schedule(self) -> List[Dict[str, Any]]:
        return list(self._safe_read(self.schedule_path, []))

    def load_processing_times(self) -> Dict[str, int]:
        return dict(self._safe_read(self.processing_time_path, {}))

    def load_materials_usage(self) -> Dict[str, Dict[str, int]]:
        return dict(self._safe_read(self.materials_usage_path, {}))

    def load_materials_available(self) -> Dict[str, int]:
        return dict(self._safe_read(self.materials_available_path, {}))

    def load_machine_states(self) -> Dict[str, int]:
        return dict(self._safe_read(self.machines_path, {}))

    def update_machine_state(self, machine: str, value: int) -> Dict[str, int]:
        data = self.load_machine_states()
        data[machine] = value
        self._write(self.machines_path, data)
        return data

    def append_schedule_entry(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        data = self.load_schedule()
        data.append(entry)
        self._write(self.schedule_path, data)
        return data


def get_data_store() -> JSONDataStore:
    """Factory helper used by dependency injection."""

    return JSONDataStore()
