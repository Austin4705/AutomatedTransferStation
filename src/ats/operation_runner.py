"""
Operation Runner — a state machine for long-running transfer station operations.

Provides:
- Queued execution of operations (one at a time)
- States: IDLE → RUNNING → PAUSED → COMPLETED / CANCELLED / FAILED
- Progress reporting via callbacks
- Thread-safe pause / resume / cancel
"""

from __future__ import annotations

import enum
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from queue import Queue

from .logger import Logger


class OperationState(enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class OperationProgress:
    """Immutable snapshot of operation progress."""
    operation_name: str
    state: OperationState
    current_step: int
    total_steps: int
    message: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def percent(self) -> float:
        if self.total_steps <= 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100.0)

    def to_dict(self) -> dict:
        return {
            "operation_name": self.operation_name,
            "state": self.state.value,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "percent": round(self.percent, 1),
            "message": self.message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error": self.error,
        }


class OperationContext:
    """
    Passed to every operation function so it can report progress and
    check for cancellation in a structured way.
    """

    def __init__(self, name: str, total_steps: int, runner: "OperationRunner"):
        self._name = name
        self._total_steps = total_steps
        self._current_step = 0
        self._runner = runner
        self._message = ""
        self._started_at = datetime.now()

    @property
    def is_cancelled(self) -> bool:
        return self._runner._cancel_event.is_set()

    def wait_if_paused(self, timeout: float = 0.1) -> bool:
        """Block while paused. Returns False if cancelled."""
        while not self._runner._cancel_event.is_set():
            if self._runner._run_event.wait(timeout=timeout):
                return True
        return False

    def check_cancelled(self) -> None:
        """Raise OperationCancelled if cancel was requested."""
        if self.is_cancelled:
            raise OperationCancelled(self._name)

    def advance(self, message: str = "") -> None:
        """Advance progress by one step and report."""
        self.check_cancelled()
        self.wait_if_paused()
        self._current_step += 1
        self._message = message
        self._runner._report_progress(self._snapshot())

    def set_progress(self, step: int, message: str = "") -> None:
        """Jump to a specific step."""
        self.check_cancelled()
        self._current_step = step
        self._message = message
        self._runner._report_progress(self._snapshot())

    def log(self, message: str) -> None:
        """Log a message (goes to Logger + progress)."""
        self._message = message
        Logger.log(f"[{self._name}] {message}")

    def _snapshot(self) -> OperationProgress:
        return OperationProgress(
            operation_name=self._name,
            state=self._runner.state,
            current_step=self._current_step,
            total_steps=self._total_steps,
            message=self._message,
            started_at=self._started_at,
        )


class OperationCancelled(Exception):
    """Raised inside an operation when cancellation is requested."""
    def __init__(self, operation_name: str):
        super().__init__(f"Operation '{operation_name}' was cancelled")
        self.operation_name = operation_name


# Type for an operation callable: fn(context, data) -> Any
OperationFn = Callable[[OperationContext, dict], Any]


class OperationRunner:
    """
    Manages queued execution of long-running operations.

    Usage::

        runner = OperationRunner()
        runner.on_progress(my_progress_callback)
        runner.submit("trace_over", trace_over_fn, data, total_steps=500)
        # ...later...
        runner.pause()
        runner.resume()
        runner.cancel()
    """

    def __init__(self):
        self._state = OperationState.IDLE
        self._state_lock = threading.Lock()
        self._run_event = threading.Event()
        self._cancel_event = threading.Event()
        self._run_event.set()  # start running

        self._queue: Queue[tuple[str, OperationFn, dict, int]] = Queue()
        self._progress_listeners: list[Callable[[OperationProgress], None]] = []
        self._current_thread: Optional[threading.Thread] = None
        self._last_progress: Optional[OperationProgress] = None

        # Start the queue consumer thread
        self._consumer = threading.Thread(target=self._consume_queue, daemon=True)
        self._consumer.start()

    # --------------- public API ---------------

    @property
    def state(self) -> OperationState:
        with self._state_lock:
            return self._state

    @property
    def last_progress(self) -> Optional[OperationProgress]:
        return self._last_progress

    def submit(self, name: str, fn: OperationFn, data: dict, total_steps: int = 0) -> None:
        """Enqueue an operation for execution."""
        self._queue.put((name, fn, data, total_steps))
        Logger.log(f"[OperationRunner] Queued operation: {name}")

    def pause(self) -> None:
        with self._state_lock:
            if self._state == OperationState.RUNNING:
                self._state = OperationState.PAUSED
                self._run_event.clear()
                Logger.log("[OperationRunner] Paused")

    def resume(self) -> None:
        with self._state_lock:
            if self._state == OperationState.PAUSED:
                self._state = OperationState.RUNNING
                self._run_event.set()
                Logger.log("[OperationRunner] Resumed")

    def cancel(self) -> None:
        """Cancel the current operation (if any). Queued operations are discarded."""
        self._cancel_event.set()
        self._run_event.set()  # unblock paused threads
        # Drain the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                break
        Logger.log("[OperationRunner] Cancel requested")

    def on_progress(self, listener: Callable[[OperationProgress], None]) -> Callable:
        """Register a progress listener. Returns an unsubscribe function."""
        self._progress_listeners.append(listener)
        def unsubscribe():
            if listener in self._progress_listeners:
                self._progress_listeners.remove(listener)
        return unsubscribe

    # --------------- internal ---------------

    def _set_state(self, new_state: OperationState):
        with self._state_lock:
            self._state = new_state

    def _report_progress(self, progress: OperationProgress):
        self._last_progress = progress
        for listener in self._progress_listeners:
            try:
                listener(progress)
            except Exception:
                pass

    def _consume_queue(self):
        """Background thread that pulls operations from the queue one at a time."""
        while True:
            name, fn, data, total_steps = self._queue.get()
            self._cancel_event.clear()
            self._run_event.set()
            self._set_state(OperationState.RUNNING)

            ctx = OperationContext(name, total_steps, self)
            started_at = datetime.now()

            self._report_progress(OperationProgress(
                operation_name=name,
                state=OperationState.RUNNING,
                current_step=0,
                total_steps=total_steps,
                message="Starting...",
                started_at=started_at,
            ))

            try:
                fn(ctx, data)
                self._set_state(OperationState.COMPLETED)
                self._report_progress(OperationProgress(
                    operation_name=name,
                    state=OperationState.COMPLETED,
                    current_step=total_steps,
                    total_steps=total_steps,
                    message="Completed",
                    started_at=started_at,
                    finished_at=datetime.now(),
                ))
                Logger.log(f"[OperationRunner] Operation '{name}' completed")

            except OperationCancelled:
                self._set_state(OperationState.CANCELLED)
                self._report_progress(OperationProgress(
                    operation_name=name,
                    state=OperationState.CANCELLED,
                    current_step=ctx._current_step,
                    total_steps=total_steps,
                    message="Cancelled",
                    started_at=started_at,
                    finished_at=datetime.now(),
                ))
                Logger.log(f"[OperationRunner] Operation '{name}' cancelled")

            except Exception as e:
                self._set_state(OperationState.FAILED)
                tb = traceback.format_exc()
                self._report_progress(OperationProgress(
                    operation_name=name,
                    state=OperationState.FAILED,
                    current_step=ctx._current_step,
                    total_steps=total_steps,
                    message=f"Failed: {e}",
                    started_at=started_at,
                    finished_at=datetime.now(),
                    error=tb,
                ))
                Logger.log_error(f"[OperationRunner] Operation '{name}' failed: {e}")

            finally:
                self._cancel_event.clear()
                self._run_event.set()
                self._set_state(OperationState.IDLE)


