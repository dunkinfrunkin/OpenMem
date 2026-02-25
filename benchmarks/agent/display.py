"""Pretty-print agent benchmark results."""
from __future__ import annotations

from .runner import AgentBenchmarkResult


def print_agent_results(
    results: list[AgentBenchmarkResult],
    scenario_names: list[str],
) -> None:
    acol = 24
    scol = 10

    print("\n" + "=" * 80)
    print("AGENT BENCHMARK RESULTS")
    print("=" * 80)

    for scenario_name in scenario_names:
        print(f"\n--- {scenario_name} ---")
        header = (
            f"{'Adapter':<{acol}} "
            f"{'Correct':>{scol}} {'Complete':>{scol}} {'NoHalluc':>{scol}} "
            f"{'Overall':>{scol}} {'Recalls':>{scol}} {'MemLat':>{scol}} {'TotalLat':>{scol}}"
        )
        print(header)
        print("-" * len(header))

        for result in results:
            sr = result.scenario_results.get(scenario_name)
            if not sr:
                continue
            if sr.skipped:
                print(f"{result.adapter_name:<{acol}} (skipped)")
                continue

            j = sr.judge_result
            a = sr.agent_result
            if not j or not a:
                print(f"{result.adapter_name:<{acol}} (no result)")
                continue

            mem_lat = sum(a.recall_latencies_ms) if a.recall_latencies_ms else 0
            print(
                f"{result.adapter_name:<{acol}} "
                f"{j.correctness:>{scol}.2f} "
                f"{j.completeness:>{scol}.2f} "
                f"{j.no_hallucination:>{scol}.2f} "
                f"{j.overall:>{scol}.2f} "
                f"{a.recall_calls:>{scol}} "
                f"{mem_lat:>{scol - 2}.0f}ms "
                f"{a.total_latency_ms:>{scol - 2}.0f}ms"
            )


def print_agent_summary(results: list[AgentBenchmarkResult]) -> None:
    print("\n" + "=" * 80)
    print("AGENT BENCHMARK SUMMARY")
    print("=" * 80)

    for result in results:
        active = [
            sr for sr in result.scenario_results.values()
            if not sr.skipped and sr.judge_result and sr.agent_result
        ]
        if not active:
            print(f"\n  {result.adapter_name}: all scenarios skipped")
            continue

        n = len(active)
        avg_correct = sum(sr.judge_result.correctness for sr in active) / n
        avg_complete = sum(sr.judge_result.completeness for sr in active) / n
        avg_no_halluc = sum(sr.judge_result.no_hallucination for sr in active) / n
        avg_overall = sum(sr.judge_result.overall for sr in active) / n
        avg_recalls = sum(sr.agent_result.recall_calls for sr in active) / n
        avg_mem_lat = sum(sum(sr.agent_result.recall_latencies_ms) for sr in active) / n
        avg_total_lat = sum(sr.agent_result.total_latency_ms for sr in active) / n

        print(f"\n  {result.adapter_name}:")
        print(f"    Avg Correctness:     {avg_correct:.3f}")
        print(f"    Avg Completeness:    {avg_complete:.3f}")
        print(f"    Avg No Hallucinate:  {avg_no_halluc:.3f}")
        print(f"    Avg Overall Score:   {avg_overall:.3f}")
        print(f"    Avg Recall Calls:    {avg_recalls:.1f}")
        print(f"    Avg Memory Latency:  {avg_mem_lat:.0f}ms")
        print(f"    Avg Total Latency:   {avg_total_lat:.0f}ms")
        print(f"    Scenarios run:       {n}/{len(result.scenario_results)}")


def print_agent_detail(results: list[AgentBenchmarkResult]) -> None:
    """Print detailed per-scenario info including key facts found/missing."""
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    for result in results:
        for name, sr in result.scenario_results.items():
            if sr.skipped or not sr.judge_result:
                continue

            j = sr.judge_result
            a = sr.agent_result
            print(f"\n  [{result.adapter_name}] {name}")
            print(f"    Score: {j.overall:.2f} (correct={j.correctness:.2f}, complete={j.completeness:.2f}, noHalluc={j.no_hallucination:.2f})")
            if j.key_facts_found:
                print(f"    Found:   {', '.join(str(f) for f in j.key_facts_found)}")
            if j.key_facts_missing:
                print(f"    Missing: {', '.join(str(f) for f in j.key_facts_missing)}")
            if j.reasoning:
                print(f"    Judge:   {j.reasoning}")
            if a:
                print(f"    Recalls: {a.recall_calls}, MemLat: {sum(a.recall_latencies_ms):.0f}ms, Total: {a.total_latency_ms:.0f}ms")
