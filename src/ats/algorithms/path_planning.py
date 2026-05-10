"""Path planning for raster scans across a sample.

Pure geometry — no hardware, no I/O. Given start/end coordinates and a
step size, return the list of (x, y) points to visit.
"""
from typing import List, Tuple


def serpentine_grid(
    start_x: float,
    end_x: float,
    start_y: float,
    end_y: float,
    step_x: float,
    step_y: float,
) -> List[Tuple[float, float]]:
    """Boustrophedon raster: each row alternates direction.

    Avoids the wasted return-stroke of a pure raster — at the end of each
    row the stage is already near the start of the next row's first point.

    Step counts are integer, computed from |end - start| / step. The first
    row begins at start_x; subsequent rows alternate.
    """
    x_steps = int(abs(end_x - start_x) / step_x)
    y_steps = int(abs(end_y - start_y) / step_y)
    y_sign = 1 if end_y >= start_y else -1

    # Preserved from original: this flag is true when the next move should
    # *decrease* x. The original code called it `going_right`, which is the
    # opposite of what it does — kept the behavior, fixed the name.
    decreasing_x = start_x >= end_x
    current_x = start_x

    points: List[Tuple[float, float]] = []
    for y in range(y_steps + 1):
        row_y = start_y + (y * step_y * y_sign)
        points.append((current_x, row_y))
        for _ in range(1, x_steps + 1):
            current_x = current_x - step_x if decreasing_x else current_x + step_x
            points.append((current_x, row_y))
        decreasing_x = not decreasing_x

    return points
