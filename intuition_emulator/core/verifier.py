from __future__ import annotations
from typing import List, Tuple
import yaml
from pathlib import Path


_DEFAULT_RULES_PATH = Path(__file__).parent.parent / "config" / "verifier_rules.yaml"


class RuleVerifier:
    """Rule-based verifier returning +1 (compatible), 0 (unclear), -1 (incompatible).
    A hard rejection occurs when incompatibility is found with a highly active claim (A > 0.7).
    """

    def __init__(self, rules_path: Path | str | None = None):
        path = Path(rules_path) if rules_path else _DEFAULT_RULES_PATH
        with open(path) as f:
            rules = yaml.safe_load(f)
        self.contradiction_pairs: List[Tuple[str, str]] = [
            tuple(p) for p in rules.get("contradiction_pairs", [])
        ]
        self.support_pairs: List[Tuple[str, str]] = [
            tuple(p) for p in rules.get("support_pairs", [])
        ]

    def _tags_contradict(self, tags_a: List[str], tags_b: List[str]) -> bool:
        for t1, t2 in self.contradiction_pairs:
            if (t1 in tags_a and t2 in tags_b) or (t2 in tags_a and t1 in tags_b):
                return True
        return False

    def _tags_support(self, tags_a: List[str], tags_b: List[str]) -> bool:
        for t1, t2 in self.support_pairs:
            if (t1 in tags_a and t2 in tags_b) or (t2 in tags_a and t1 in tags_b):
                return True
        return False

    def verify(
        self,
        candidate_tags: List[str],
        active_claims,  # list of ClaimState
        high_activation_threshold: float = 0.7,
    ) -> Tuple[int, bool]:
        """
        Returns (signal, is_hard):
          signal: +1, 0, or -1
          is_hard: True if incompatibility is with a highly active claim
        """
        hard = False
        any_support = False
        any_conflict = False

        for claim in active_claims:
            if self._tags_contradict(candidate_tags, claim.tags):
                any_conflict = True
                if claim.A > high_activation_threshold:
                    hard = True
            elif self._tags_support(candidate_tags, claim.tags):
                any_support = True

        if any_conflict:
            return -1, hard
        if any_support:
            return 1, False
        return 0, False
