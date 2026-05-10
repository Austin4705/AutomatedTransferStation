"""Hardware-facing protocols used by motion-bound algorithms.

Algorithms in this package depend on these structural interfaces, not on
the concrete `Transfer_Station` / `Camera` classes. Anything that exposes
the listed methods can be passed in — including mocks for tests.
"""
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Stage(Protocol):
    """Minimal motion-stage interface used by autofocus and scan algorithms."""

    def posZ(self) -> float: ...
    def moveZ(self, z: float) -> None: ...
    def moveZRel(self, dz: float) -> None: ...
    def moveXY(self, x: float, y: float) -> None: ...
    def wait(self, seconds: float) -> None: ...


@runtime_checkable
class FrameSource(Protocol):
    """Anything that can return the current frame as an HxWx3 numpy array."""

    def get_frame(self) -> np.ndarray: ...
