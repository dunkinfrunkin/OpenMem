from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable

from .adapters.base import RecallResult


@dataclass
class QueryMetrics:
    """Metrics for a single query."""

    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    ndcg_at_k: float = 0.0
    mrr: float = 0.0
    latency_ms: float = 0.0


@dataclass
class ScenarioMetrics:
    """Aggregated metrics for an entire scenario."""

    avg_precision: float = 0.0
    avg_recall: float = 0.0
    avg_ndcg: float = 0.0
    avg_mrr: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    per_query: list[QueryMetrics] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if k == 0:
        return 0.0
    hits = sum(1 for rid in retrieved_ids[:k] if rid in relevant_ids)
    return hits / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    hits = sum(1 for rid in retrieved_ids[:k] if rid in relevant_ids)
    return hits / len(relevant_ids)


def dcg_at_k(retrieved_ids: list[str], relevance_grades: dict[str, int], k: int) -> float:
    dcg = 0.0
    for i, rid in enumerate(retrieved_ids[:k]):
        grade = relevance_grades.get(rid, 0)
        dcg += (2**grade - 1) / math.log2(i + 2)
    return dcg


def ndcg_at_k(
    retrieved_ids: list[str], relevance_grades: dict[str, int], k: int
) -> float:
    actual_dcg = dcg_at_k(retrieved_ids, relevance_grades, k)
    ideal_ids = sorted(
        relevance_grades.keys(), key=lambda x: relevance_grades[x], reverse=True
    )
    ideal_dcg = dcg_at_k(ideal_ids, relevance_grades, k)
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = (p / 100.0) * (len(sorted_v) - 1)
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return sorted_v[lower]
    frac = idx - lower
    return sorted_v[lower] * (1 - frac) + sorted_v[upper] * frac


def evaluate_query(
    recall_fn: Callable[[str, int], list[RecallResult]],
    query: str,
    relevant_ids: set[str],
    relevance_grades: dict[str, int] | None,
    top_k: int,
) -> QueryMetrics:
    start = time.perf_counter()
    results = recall_fn(query, top_k)
    elapsed_ms = (time.perf_counter() - start) * 1000

    retrieved_ids = [r.id for r in results]
    grades = relevance_grades or {rid: 1 for rid in relevant_ids}

    return QueryMetrics(
        precision_at_k=precision_at_k(retrieved_ids, relevant_ids, top_k),
        recall_at_k=recall_at_k(retrieved_ids, relevant_ids, top_k),
        ndcg_at_k=ndcg_at_k(retrieved_ids, grades, top_k),
        mrr=mrr(retrieved_ids, relevant_ids),
        latency_ms=elapsed_ms,
    )


def aggregate_query_metrics(query_metrics: list[QueryMetrics]) -> ScenarioMetrics:
    if not query_metrics:
        return ScenarioMetrics()

    n = len(query_metrics)
    latencies = [qm.latency_ms for qm in query_metrics]

    return ScenarioMetrics(
        avg_precision=sum(qm.precision_at_k for qm in query_metrics) / n,
        avg_recall=sum(qm.recall_at_k for qm in query_metrics) / n,
        avg_ndcg=sum(qm.ndcg_at_k for qm in query_metrics) / n,
        avg_mrr=sum(qm.mrr for qm in query_metrics) / n,
        latency_p50_ms=percentile(latencies, 50),
        latency_p95_ms=percentile(latencies, 95),
        latency_p99_ms=percentile(latencies, 99),
        per_query=query_metrics,
    )
