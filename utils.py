from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any

import pandas as pd

# -----------------
# Logging utilities
# -----------------

def get_logger(name: str = "drug_conflict_detection") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger

logger = get_logger()

# -----------------
# Data utilities
# -----------------

def read_csv_records(path: Path | str) -> List[dict]:
    path = Path(path)
    df = pd.read_csv(path)
    # Normalize string list fields with ';' separator into Python lists where appropriate
    records: List[dict] = []
    for row in df.to_dict(orient="records"):
        rec = {}
        for k, v in row.items():
            if isinstance(v, str) and ";" in v:
                rec[k] = [x.strip() for x in v.split(";") if x and x.strip().lower() != "none"]
            else:
                rec[k] = v
        records.append(rec)
    return records

# -----------------
# Severity utilities
# -----------------

SEVERITY_SCORES = {
    "Major": 3,
    "Moderate": 2,
    "Minor": 1,
}

def severity_to_score(severity: str) -> int:
    return SEVERITY_SCORES.get(str(severity).title(), 0)

# -----------------
# Knowledge base
# -----------------

def _normalize_key(*parts: str) -> Tuple[str, ...]:
    return tuple(p.strip().lower() for p in parts)

@dataclass(frozen=True)
class Rule:
    rtype: str  # 'drug-drug' | 'drug-condition'
    item_a: str
    item_b: str
    severity: str
    recommendation: str
    notes: str | None = None

    @property
    def key(self) -> Tuple[str, str, str]:
        if self.rtype == "drug-drug":
            a, b = sorted([self.item_a, self.item_b], key=lambda s: s.lower())
            return (self.rtype, a.lower(), b.lower())
        else:
            # Keep condition first for drug-condition
            return (self.rtype, self.item_a.lower(), self.item_b.lower())


def build_rules_kb(rules_rows: Iterable[dict]) -> Dict[Tuple[str, str, str], Rule]:
    kb: Dict[Tuple[str, str, str], Rule] = {}
    for r in rules_rows:
        rule = Rule(
            rtype=str(r.get("type", "")).strip(),
            item_a=str(r.get("item_a", "")).strip(),
            item_b=str(r.get("item_b", "")).strip(),
            severity=str(r.get("severity", "")).strip().title(),
            recommendation=str(r.get("recommendation", "")).strip(),
            notes=str(r.get("notes", "")).strip() or None,
        )
        kb[rule.key] = rule
    return kb

# -----------------
# Best-First Search (BFS)
# -----------------

@dataclass
class Conflict:
    rtype: str
    item_a: str
    item_b: str
    severity: str
    recommendation: str
    score: int


def make_condition_tokens(conditions: Iterable[str], allergies: Iterable[str] | None = None) -> List[str]:
    tokens = [str(c).strip() for c in conditions if str(c).strip()]
    if allergies:
        # Guard against scalar (float/str)
        if isinstance(allergies, (str, float, int)):
            allergies = [allergies]
        for a in allergies:
            a = str(a).strip()
            if a and a.lower() != "none":
                tokens.append(f"{a}Allergy")
    return tokens


def bfs_conflicts(prescription: List[str], conditions: List[str], kb: Dict[Tuple[str, str, str], Rule]) -> List[Conflict]:
    """
    Best-First Search over potential conflict nodes prioritized by severity.

    - Nodes: concrete (rtype, item_a, item_b) that exist in KB given current prescription and conditions.
    - Priority: severity score (Major > Moderate > Minor).
    - Expansion: trivial (no deeper graph), processed in priority order to mimic best-first evaluation.
    """
    # Generate candidate nodes from current state
    drugs = [d.strip() for d in prescription if d and str(d).strip()]
    conditions = [c.strip() for c in conditions if c and str(c).strip()]

    # Build candidate keys
    candidate_keys: List[Tuple[str, str, str]] = []

    # drug-drug pairs
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            a, b = sorted([drugs[i], drugs[j]], key=lambda s: s.lower())
            k = ("drug-drug", a.lower(), b.lower())
            if k in kb:
                candidate_keys.append(k)

    # drug-condition pairs
    for c in conditions:
        for d in drugs:
            k = ("drug-condition", c.lower(), d.lower())
            if k in kb:
                candidate_keys.append(k)

    # Priority queue
    heap: List[Tuple[int, int, Tuple[str, str, str]]] = []
    visited: set[Tuple[str, str, str]] = set()
    counter = 0

    for k in candidate_keys:
        rule = kb[k]
        score = severity_to_score(rule.severity)
        heapq.heappush(heap, (-score, counter, k))  # negative for max-heap behavior
        counter += 1

    results: List[Conflict] = []

    while heap:
        neg_score, _, key = heapq.heappop(heap)
        if key in visited:
            continue
        visited.add(key)
        rule = kb[key]
        results.append(
            Conflict(
                rtype=rule.rtype,
                item_a=rule.item_a,
                item_b=rule.item_b,
                severity=rule.severity,
                recommendation=rule.recommendation,
                score=severity_to_score(rule.severity),
            )
        )
        # No further expansion in this simplified BFS. In richer models, we could expand
        # into implied risks (e.g., multi-drug syndromes) or add patient-specific modifiers.

    return results


def conflicts_to_frame(conflicts: List[dict | Conflict]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for c in conflicts:
        if isinstance(c, Conflict):
            rows.append({
                "type": c.rtype,
                "item_a": c.item_a,
                "item_b": c.item_b,
                "severity": c.severity,
                "score": c.score,
                "recommendation": c.recommendation,
            })
        else:
            rows.append(dict(c))
    return pd.DataFrame(rows)

# -----------------
# Optional plotting
# -----------------

def plot_severity_distribution(conflicts_df: pd.DataFrame):
    """Plot a simple severity distribution bar chart.

    Optional helper migrated from visualization.py to keep code centralized.
    Uses lazy imports so normal simulation runs avoid importing heavy libs.
    """
    if conflicts_df.empty:
        print("No conflicts to plot.")
        return
    try:
        import matplotlib.pyplot as plt  # type: ignore
        import seaborn as sns  # type: ignore
    except ImportError as e:
        print(f"Plot dependencies missing: {e}. Install matplotlib and seaborn.")
        return
    order = ["Major", "Moderate", "Minor"]
    counts = conflicts_df["severity"].value_counts()
    data = pd.DataFrame({"severity": counts.index, "count": counts.values})
    data = data.set_index("severity").reindex(order).fillna(0).reset_index()
    plt.figure(figsize=(6, 4))
    sns.barplot(x="severity", y="count", data=data, order=order, palette="Reds")
    plt.title("Conflict Severity Distribution")
    plt.xlabel("Severity")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()
