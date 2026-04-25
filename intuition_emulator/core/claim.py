from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class ClaimState:
    claim_id: str
    tags: List[str] = field(default_factory=list)
    R: float = 0.5
    P: float = 0.5
    H: float = 5.0
    A: float = 0.5
    status: str = "latent"  # "aktiv" | "latent" | "verworfen"
    P_history: List[float] = field(default_factory=list)
    max_R: float = 0.0
    age: int = 0
    stability: float = 1.0
    projection_count: int = 0
    verifier_history: List[int] = field(default_factory=list)
    neighbor_ids: List[str] = field(default_factory=list)
    verifier_exempt: bool = False  # if True: used as reference in verifier but never itself checked
    trust: float = 0.0             # T: accumulated verifier-weighted reliability (starts at 0, earned over time)

    def __post_init__(self):
        # Only set max_R from initial R if it was not explicitly provided higher
        if self.max_R < self.R:
            self.max_R = self.R
        self.P_history = list(self.P_history)

    def is_projection_ready(self, params: dict) -> bool:
        return (
            self.status == "aktiv"
            and self.P >= params["theta_proj"]
            and self.R >= params["theta_R"]
            and self.stability >= params["theta_S"]
        )

    def record_verifier(self, v: int):
        self.verifier_history.append(v)

    def last_n_verifier_sum(self, n: int = 3) -> float:
        recent = self.verifier_history[-n:] if len(self.verifier_history) >= n else self.verifier_history
        return sum(recent)
