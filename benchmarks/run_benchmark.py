#!/usr/bin/env python3
"""CLI entry point for running OpenMem benchmarks.

Usage:
    python -m benchmarks.run_benchmark
    python -m benchmarks.run_benchmark --adapters openmem chromadb
    python -m benchmarks.run_benchmark --scenarios basic_recall graph_boosted
    python -m benchmarks.run_benchmark --verbose --json
"""
from __future__ import annotations

import argparse
import json
import sys

from .adapters import ADAPTER_REGISTRY
from .display import print_feature_matrix, print_results_table, print_summary
from .runner import run_all
from .scenarios.scenarios import all_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark OpenMem against alternative memory systems",
    )
    parser.add_argument(
        "--adapters",
        nargs="+",
        choices=list(ADAPTER_REGISTRY.keys()),
        default=None,
        help="Which adapters to benchmark (default: all available)",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=None,
        help="Which scenarios to run (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print progress as benchmarks run",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON instead of tables",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Repeat each scenario N times (averages latency)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Build adapters
    adapter_names = args.adapters or list(ADAPTER_REGISTRY.keys())
    adapters = []
    for name in adapter_names:
        try:
            adapter_cls = ADAPTER_REGISTRY[name]
            adapters.append(adapter_cls())
        except (ImportError, KeyError) as e:
            print(f"Warning: Skipping {name}: {e}", file=sys.stderr)

    if not adapters:
        print("Error: No adapters available.", file=sys.stderr)
        sys.exit(1)

    # Build scenarios
    scenarios = all_scenarios()
    if args.scenarios:
        scenario_names = set(args.scenarios)
        scenarios = [s for s in scenarios if s.name in scenario_names]
        if not scenarios:
            print("Error: No matching scenarios found.", file=sys.stderr)
            sys.exit(1)

    # Run benchmarks
    all_results = []
    for _ in range(args.repeat):
        results = run_all(adapters, scenarios, verbose=args.verbose)
        all_results.append(results)

    final_results = all_results[0]

    # Average latencies across repeated runs
    if args.repeat > 1:
        for adapter_idx, result in enumerate(final_results):
            for scenario_name, metrics in result.scenario_results.items():
                if metrics.skipped:
                    continue
                latencies = [
                    all_results[run][adapter_idx]
                    .scenario_results[scenario_name]
                    .latency_p50_ms
                    for run in range(args.repeat)
                    if not all_results[run][adapter_idx]
                    .scenario_results[scenario_name]
                    .skipped
                ]
                if latencies:
                    metrics.latency_p50_ms = sum(latencies) / len(latencies)

    # Output
    if args.json_output:
        output = _results_to_dict(final_results)
        print(json.dumps(output, indent=2))
    else:
        scenario_names = [s.name for s in scenarios]
        print_results_table(final_results, scenario_names)
        print_feature_matrix(adapters)
        print_summary(final_results)


def _results_to_dict(results: list) -> dict:
    output = {}
    for result in results:
        adapter_data = {}
        for name, metrics in result.scenario_results.items():
            if metrics.skipped:
                adapter_data[name] = {"skipped": True, "reason": metrics.skip_reason}
            else:
                adapter_data[name] = {
                    "precision_at_k": round(metrics.avg_precision, 4),
                    "recall_at_k": round(metrics.avg_recall, 4),
                    "ndcg_at_k": round(metrics.avg_ndcg, 4),
                    "mrr": round(metrics.avg_mrr, 4),
                    "latency_p50_ms": round(metrics.latency_p50_ms, 2),
                    "latency_p95_ms": round(metrics.latency_p95_ms, 2),
                    "latency_p99_ms": round(metrics.latency_p99_ms, 2),
                }
        output[result.adapter_name] = adapter_data
    return output


if __name__ == "__main__":
    main()
