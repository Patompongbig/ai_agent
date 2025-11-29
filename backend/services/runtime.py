"""Background helpers for tracking machine countdowns."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
import threading
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from .data_store import JSONDataStore, get_data_store

logger = logging.getLogger(__name__)

CompletionCallback = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass
class MachineRuntimeManager:
    """Tracks running machine jobs and flips state back when done."""

    store: JSONDataStore = field(default_factory=get_data_store)
    _tasks: Dict[str, asyncio.Task] = field(default_factory=dict, init=False)
    _callback: Optional[CompletionCallback] = field(default=None, init=False)
    _start_times: Dict[str, float] = field(default_factory=dict, init=False)
    _durations: Dict[str, float] = field(default_factory=dict, init=False)

    def register_completion_callback(self, callback: CompletionCallback) -> None:
        self._callback = callback

    def start_job(
        self,
        machine: str,
        duration_seconds: int,
        payload: Dict[str, Any],
    ) -> None:
        """Set machine to busy and start countdown until completion."""

        self.store.update_machine_state(machine, 0)
        self._cancel_existing(machine)
        self._start_times[machine] = time.monotonic()

        duration_seconds = max(0, duration_seconds)
        try:
            loop = asyncio.get_running_loop()
            self._tasks[machine] = loop.create_task(
                self._run_job(machine, duration_seconds, payload)
            )
        except RuntimeError:
            logger.warning(
                "No running event loop found; spawning a background loop for %s",
                machine,
            )
            thread = threading.Thread(
                target=self._run_in_new_loop,
                args=(machine, duration_seconds, payload),
                daemon=True,
            )
            thread.start()

    def _cancel_existing(self, machine: str) -> None:
        task = self._tasks.pop(machine, None)
        if task:
            task.cancel()

    def _run_in_new_loop(
        self, machine: str, duration_seconds: int, payload: Dict[str, Any]
    ) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self._run_job(machine, duration_seconds, payload)
            )
        finally:
            loop.close()

    async def _run_job(
        self,
        machine: str,
        duration_seconds: int,
        payload: Dict[str, Any],
    ) -> None:
        try:
            await asyncio.sleep(duration_seconds)
        except asyncio.CancelledError:
            logger.info("Cancelled runtime tracker for %s", machine)
            return

        self.store.update_machine_state(machine, 1)
        start_time = self._start_times.pop(machine, None)
        if start_time is not None:
            elapsed = time.monotonic() - start_time
            self._durations[machine] = self._durations.get(machine, 0.0) + elapsed

        schedule = self.store.load_schedule()
        callback_payload = {
            **payload,
            "machine": machine,
            "schedule": schedule,
            "schedule_text": json.dumps(schedule, indent=2),
        }
        if self._callback:
            try:
                await self._callback(callback_payload)
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("Machine completion callback failed for %s", machine)

    def summarize(self) -> Dict[str, float]:
        return dict(self._durations)


def get_runtime_manager() -> MachineRuntimeManager:
    return MachineRuntimeManager()


runtime_manager = MachineRuntimeManager()
