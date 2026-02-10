"""Tests for the OperationRunner state machine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import time
import threading
import pytest
from unittest.mock import MagicMock

# Mock Logger before importing operation_runner
from logger import Logger
Logger.socket_manager = MagicMock()

from operation_runner import OperationRunner, OperationState, OperationCancelled, OperationContext


class TestOperationRunner:

    def setup_method(self):
        self.runner = OperationRunner()
        self.progress_log = []
        self.runner.on_progress(lambda p: self.progress_log.append(p))

    def test_initial_state_is_idle(self):
        assert self.runner.state == OperationState.IDLE

    def test_simple_operation_completes(self):
        def my_op(ctx: OperationContext, data: dict):
            for i in range(3):
                ctx.advance(f"Step {i}")
            assert data["key"] == "value"

        self.runner.submit("test_op", my_op, {"key": "value"}, total_steps=3)
        time.sleep(1)  # Allow operation to complete

        assert self.runner.state == OperationState.IDLE
        # Check that we got progress reports
        assert len(self.progress_log) >= 3
        # Last progress should be COMPLETED
        final = self.progress_log[-1]
        assert final.state == OperationState.COMPLETED

    def test_cancel_operation(self):
        started = threading.Event()

        def slow_op(ctx: OperationContext, data: dict):
            started.set()
            for i in range(100):
                ctx.advance(f"Step {i}")
                time.sleep(0.05)

        self.runner.submit("slow_op", slow_op, {}, total_steps=100)
        started.wait(timeout=2)
        self.runner.cancel()
        time.sleep(0.5)

        assert self.runner.state == OperationState.IDLE
        # Should have a CANCELLED progress entry
        cancelled = [p for p in self.progress_log if p.state == OperationState.CANCELLED]
        assert len(cancelled) >= 1

    def test_pause_resume(self):
        paused_at_step = []

        def pausable_op(ctx: OperationContext, data: dict):
            for i in range(5):
                ctx.advance(f"Step {i}")
                paused_at_step.append(i)
                time.sleep(0.05)

        self.runner.submit("pausable", pausable_op, {}, total_steps=5)
        time.sleep(0.1)
        self.runner.pause()
        assert self.runner.state == OperationState.PAUSED
        steps_at_pause = len(paused_at_step)
        time.sleep(0.3)
        # Should not have progressed while paused
        assert len(paused_at_step) == steps_at_pause

        self.runner.resume()
        time.sleep(1)
        assert self.runner.state == OperationState.IDLE

    def test_failed_operation(self):
        def failing_op(ctx: OperationContext, data: dict):
            raise RuntimeError("Something went wrong")

        self.runner.submit("fail_op", failing_op, {}, total_steps=1)
        time.sleep(0.5)

        assert self.runner.state == OperationState.IDLE
        failed = [p for p in self.progress_log if p.state == OperationState.FAILED]
        assert len(failed) >= 1
        assert "Something went wrong" in failed[0].error


class TestConfig:
    """Test config validation."""

    def test_app_config_from_env(self):
        from config import AppConfig
        os.environ["TRANSFER_STATION_TYPE"] = "virtual"
        os.environ["CAMERA_TYPE"] = "virtual"
        config = AppConfig.from_env()
        assert config.station.station_type == "virtual"
        assert config.camera.camera_type == "virtual"
        assert config.camera.max_cameras >= 1


