"""Decide when to re-run autofocus during a raster scan.

The trace-over loop runs autofocus only when:
  - the current frame's background looks like substrate (purple SiO2), AND
  - either the edge count is below threshold (suggesting it has drifted out
    of focus), or the previous frame was *not* on substrate (so we just
    came out of a non-substrate region and need to re-focus).

Returning False on non-substrate frames is intentional — autofocus relies
on edge count, which is meaningless on bare-metal or off-wafer regions.
"""


def should_autofocus(
    *,
    is_substrate_background: bool,
    edge_count: int,
    prev_was_not_substrate: bool,
    edge_threshold: int = 10,
) -> bool:
    if not is_substrate_background:
        return False
    return edge_count < edge_threshold or prev_was_not_substrate
