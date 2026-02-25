from __future__ import annotations

from dataclasses import dataclass, field

from .adapters.base import MemoryAdapter
from .metrics import ScenarioMetrics, aggregate_query_metrics, evaluate_query
from .scenarios.scenarios import Scenario


@dataclass
class BenchmarkResult:
    adapter_name: str
    scenario_results: dict[str, ScenarioMetrics] = field(default_factory=dict)


def _should_skip(adapter: MemoryAdapter, scenario: Scenario) -> str | None:
    caps = adapter.capabilities
    if scenario.requires_graph and not caps.supports_graph:
        return f"{adapter.name} does not support graph features"
    if scenario.requires_contradiction and not caps.supports_contradiction:
        return f"{adapter.name} does not support contradiction resolution"
    if scenario.requires_supersession and not caps.supports_supersession:
        return f"{adapter.name} does not support supersession"
    return None


def _apply_temporal_offset(adapter: MemoryAdapter, memory_def, age_days: int) -> None:
    """Backdate memory timestamps for adapters that support it."""
    if age_days <= 0:
        return

    from .adapters.bm25_only_adapter import BM25OnlyAdapter
    from .adapters.openmem_adapter import OpenMemAdapter

    if isinstance(adapter, (OpenMemAdapter, BM25OnlyAdapter)):
        internal_id = adapter._id_map.get(memory_def.id)
        if internal_id and adapter._engine:
            mem = adapter._engine.store.get_memory(internal_id)
            if mem:
                offset = age_days * 86400
                mem.created_at -= offset
                mem.updated_at -= offset
                adapter._engine.store.update_memory(mem)


def run_scenario(adapter: MemoryAdapter, scenario: Scenario) -> ScenarioMetrics:
    skip_reason = _should_skip(adapter, scenario)
    if skip_reason:
        return ScenarioMetrics(skipped=True, skip_reason=skip_reason)

    try:
        adapter.setup()
    except ImportError as e:
        return ScenarioMetrics(skipped=True, skip_reason=str(e))

    try:
        # Store all memories
        for mem_def in scenario.memories:
            adapter.store(mem_def.id, mem_def.text, mem_def.metadata)

        # Apply temporal offsets
        for mem_def in scenario.memories:
            age_days = (mem_def.metadata or {}).get("age_days", 0)
            _apply_temporal_offset(adapter, mem_def, age_days)

        # Create links
        for link_def in scenario.links:
            adapter.link(
                link_def.source_id, link_def.target_id,
                link_def.rel_type, link_def.weight,
            )

        # Apply operations
        for op_def in scenario.operations:
            if op_def.op == "supersede":
                adapter.supersede(**op_def.args)
            elif op_def.op == "contradict":
                adapter.contradict(**op_def.args)
            elif op_def.op == "reinforce":
                adapter.reinforce(**op_def.args)

        # Run queries
        query_metrics = []
        for query_def in scenario.queries:
            qm = evaluate_query(
                recall_fn=adapter.recall,
                query=query_def.query,
                relevant_ids=set(query_def.relevant_ids),
                relevance_grades=query_def.relevance_grades,
                top_k=query_def.top_k,
            )
            query_metrics.append(qm)

        return aggregate_query_metrics(query_metrics)

    finally:
        adapter.teardown()


def run_all(
    adapters: list[MemoryAdapter],
    scenarios: list[Scenario],
    verbose: bool = False,
) -> list[BenchmarkResult]:
    results = []
    for adapter in adapters:
        if verbose:
            print(f"\n{'=' * 60}")
            print(f"  {adapter.name}")
            print(f"{'=' * 60}")

        bench_result = BenchmarkResult(adapter_name=adapter.name)
        for scenario in scenarios:
            if verbose:
                print(f"  {scenario.name:30s} ", end="", flush=True)

            metrics = run_scenario(adapter, scenario)

            if verbose:
                if metrics.skipped:
                    print(f"SKIP  ({metrics.skip_reason})")
                else:
                    print(
                        f"P@K={metrics.avg_precision:.3f}  "
                        f"R@K={metrics.avg_recall:.3f}  "
                        f"NDCG={metrics.avg_ndcg:.3f}  "
                        f"MRR={metrics.avg_mrr:.3f}  "
                        f"lat={metrics.latency_p50_ms:.1f}ms"
                    )

            bench_result.scenario_results[scenario.name] = metrics
        results.append(bench_result)

    return results
