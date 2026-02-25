#!/usr/bin/env python3
"""CLI entry point for agent-in-the-loop benchmarks.

Usage:
    python -m benchmarks.run_agent_benchmark
    python -m benchmarks.run_agent_benchmark --adapters openmem chromadb
    python -m benchmarks.run_agent_benchmark --scenarios fact_retrieval needle_retrieval
    python -m benchmarks.run_agent_benchmark --model gpt-4o --verbose --detail
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from .adapters import ADAPTER_REGISTRY
from .agent.display import print_agent_detail, print_agent_results, print_agent_summary
from .agent.harness import AgentHarness
from .agent.runner import run_agent_benchmark
from .agent.scenarios import all_agent_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent-in-the-loop benchmark: LLM agent uses memory tools to answer questions",
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
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model for the agent (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-4o-mini",
        help="OpenAI model for answer evaluation (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Max agent turns per scenario (default: 10)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print progress as benchmarks run",
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Print detailed per-scenario breakdown with key facts",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
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
    scenarios = all_agent_scenarios()
    if args.scenarios:
        scenario_names = set(args.scenarios)
        scenarios = [s for s in scenarios if s.name in scenario_names]
        if not scenarios:
            print("Error: No matching scenarios found.", file=sys.stderr)
            sys.exit(1)

    # Build harness
    harness = AgentHarness(
        model=args.model,
        max_turns=args.max_turns,
    )

    # Run
    results = run_agent_benchmark(
        adapters=adapters,
        scenarios=scenarios,
        harness=harness,
        judge_model=args.judge_model,
        verbose=args.verbose,
    )

    # Output
    if args.json_output:
        print(json.dumps(_results_to_dict(results), indent=2))
    else:
        scenario_names_list = [s.name for s in scenarios]
        print_agent_results(results, scenario_names_list)
        print_agent_summary(results)
        if args.detail:
            print_agent_detail(results)


def _results_to_dict(results: list) -> dict:
    output = {}
    for result in results:
        adapter_data = {}
        for name, sr in result.scenario_results.items():
            if sr.skipped:
                adapter_data[name] = {"skipped": True, "reason": sr.skip_reason}
            elif sr.judge_result and sr.agent_result:
                adapter_data[name] = {
                    "correctness": round(sr.judge_result.correctness, 3),
                    "completeness": round(sr.judge_result.completeness, 3),
                    "no_hallucination": round(sr.judge_result.no_hallucination, 3),
                    "overall": round(sr.judge_result.overall, 3),
                    "recall_calls": sr.agent_result.recall_calls,
                    "memory_latency_ms": round(sum(sr.agent_result.recall_latencies_ms), 1),
                    "total_latency_ms": round(sr.agent_result.total_latency_ms, 1),
                    "key_facts_found": sr.judge_result.key_facts_found,
                    "key_facts_missing": sr.judge_result.key_facts_missing,
                }
        output[result.adapter_name] = adapter_data
    return output


if __name__ == "__main__":
    main()
