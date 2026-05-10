"""Pass-through whitebalance — useful as the default pipeline stage."""
from ..registry import algorithm


@algorithm("whitebalance", "identity")
def identity(image):
    """Return the frame unchanged."""
    return image
