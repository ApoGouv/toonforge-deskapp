from dataclasses import dataclass
from typing import Any, Optional

@dataclass(frozen=True)
class PipelineStep:
    """
    Immutable data object describing a pipeline step.
    """
    key: str                 # internal identifier (e.g. "gray")
    label: str               # UI title (e.g. "Grayscale")
    image: Any               # np.ndarray
    tooltip: Optional[str] = None