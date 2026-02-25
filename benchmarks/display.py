from __future__ import annotations

from .adapters.base import MemoryAdapter
from .runner import BenchmarkResult


def print_results_table(results: list[BenchmarkResult], scenarios: list[str]) -> None:
    col = 10
    acol = 24

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)

    for scenario_name in scenarios:
        print(f"\n--- {scenario_name} ---")
        header = (
            f"{'Adapter':<{acol}} "
            f"{'P@K':>{col}} {'R@K':>{col}} {'NDCG':>{col}} "
            f"{'MRR':>{col}} {'Lat p50':>{col}}"
        )
        print(header)
        print("-" * len(header))

        for result in results:
            metrics = result.scenario_results.get(scenario_name)
            if not metrics:
                continue
            if metrics.skipped:
                print(f"{result.adapter_name:<{acol}} (skipped)")
                continue

            print(
                f"{result.adapter_name:<{acol}} "
                f"{metrics.avg_precision:>{col}.3f} "
                f"{metrics.avg_recall:>{col}.3f} "
                f"{metrics.avg_ndcg:>{col}.3f} "
                f"{metrics.avg_mrr:>{col}.3f} "
                f"{metrics.latency_p50_ms:>{col - 2}.1f}ms"
            )


def print_feature_matrix(adapters: list[MemoryAdapter]) -> None:
    features = [
        ("Graph Links", "supports_graph"),
        ("Contradiction", "supports_contradiction"),
        ("Supersession", "supports_supersession"),
        ("Temporal Decay", "supports_temporal_decay"),
        ("Reinforcement", "supports_reinforcement"),
        ("Metadata", "supports_metadata"),
    ]

    print("\n" + "=" * 80)
    print("FEATURE SUPPORT MATRIX")
    print("=" * 80)

    fcol = 16
    acol = 24
    header = f"{'Feature':<{fcol}}"
    for adapter in adapters:
        header += f" {adapter.name:>{acol}}"
    print(header)
    print("-" * len(header))

    for feat_name, attr_name in features:
        row = f"{feat_name:<{fcol}}"
        for adapter in adapters:
            supported = getattr(adapter.capabilities, attr_name, False)
            symbol = "YES" if supported else " --"
            row += f" {symbol:>{acol}}"
        print(row)


def print_summary(results: list[BenchmarkResult]) -> None:
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY (averaged across non-skipped scenarios)")
    print("=" * 80)

    for result in results:
        active = [m for m in result.scenario_results.values() if not m.skipped]
        if not active:
            print(f"  {result.adapter_name}: all scenarios skipped")
            continue

        n = len(active)
        avg_p = sum(m.avg_precision for m in active) / n
        avg_r = sum(m.avg_recall for m in active) / n
        avg_ndcg = sum(m.avg_ndcg for m in active) / n
        avg_mrr = sum(m.avg_mrr for m in active) / n
        avg_lat = sum(m.latency_p50_ms for m in active) / n

        print(f"\n  {result.adapter_name}:")
        print(f"    Avg Precision@K:  {avg_p:.3f}")
        print(f"    Avg Recall@K:     {avg_r:.3f}")
        print(f"    Avg NDCG@K:       {avg_ndcg:.3f}")
        print(f"    Avg MRR:          {avg_mrr:.3f}")
        print(f"    Avg Latency p50:  {avg_lat:.1f}ms")
        print(f"    Scenarios run:    {n}/{len(result.scenario_results)}")
