"""Orchestrator for agent-in-the-loop benchmarks.

Sets up each adapter with pre-populated memories, runs the LLM agent,
and evaluates the answer with an LLM judge.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from benchmarks.adapters.base import MemoryAdapter

from .harness import AgentHarness, AgentResult
from .judge import JudgeResult, judge_answer
from .scenarios import AgentScenario


@dataclass
class AgentScenarioResult:
    scenario_name: str
    adapter_name: str
    agent_result: AgentResult | None = None
    judge_result: JudgeResult | None = None
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class AgentBenchmarkResult:
    adapter_name: str
    scenario_results: dict[str, AgentScenarioResult] = field(default_factory=dict)


def _should_skip(adapter: MemoryAdapter, scenario: AgentScenario) -> str | None:
    caps = adapter.capabilities
    if scenario.requires_graph and not caps.supports_graph:
        return f"{adapter.name} does not support graph features"
    if scenario.requires_contradiction and not caps.supports_contradiction:
        return f"{adapter.name} does not support contradiction resolution"
    if scenario.requires_supersession and not caps.supports_supersession:
        return f"{adapter.name} does not support supersession"
    return None


def _apply_temporal_offset(adapter: MemoryAdapter, mem_def, age_days: int) -> None:
    if age_days <= 0:
        return
    from benchmarks.adapters.bm25_only_adapter import BM25OnlyAdapter
    from benchmarks.adapters.openmem_adapter import OpenMemAdapter

    if isinstance(adapter, (OpenMemAdapter, BM25OnlyAdapter)):
        internal_id = adapter._id_map.get(mem_def.id)
        if internal_id and adapter._engine:
            mem = adapter._engine.store.get_memory(internal_id)
            if mem:
                offset = age_days * 86400
                mem.created_at -= offset
                mem.updated_at -= offset
                adapter._engine.store.update_memory(mem)


def run_agent_scenario(
    adapter: MemoryAdapter,
    scenario: AgentScenario,
    harness: AgentHarness,
    judge_model: str = "gpt-4o-mini",
    verbose: bool = False,
) -> AgentScenarioResult:
    skip_reason = _should_skip(adapter, scenario)
    if skip_reason:
        return AgentScenarioResult(
            scenario_name=scenario.name,
            adapter_name=adapter.name,
            skipped=True,
            skip_reason=skip_reason,
        )

    try:
        adapter.setup()
    except ImportError as e:
        return AgentScenarioResult(
            scenario_name=scenario.name,
            adapter_name=adapter.name,
            skipped=True,
            skip_reason=str(e),
        )

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

        # Run the agent
        if verbose:
            print(f"    Running agent...", end="", flush=True)
        agent_result = harness.run(adapter, scenario.task)
        if verbose:
            print(f" {agent_result.recall_calls} recalls, {agent_result.total_latency_ms:.0f}ms total")

        # Judge the answer
        if agent_result.error:
            if verbose:
                print(f"    Agent error: {agent_result.error}")
            return AgentScenarioResult(
                scenario_name=scenario.name,
                adapter_name=adapter.name,
                agent_result=agent_result,
                skipped=True,
                skip_reason=f"Agent error: {agent_result.error}",
            )

        if verbose:
            print(f"    Judging answer...", end="", flush=True)
        judge_result = judge_answer(
            question=scenario.task,
            expected_answer=scenario.expected_answer,
            key_facts=scenario.key_facts,
            actual_answer=agent_result.answer,
            model=judge_model,
        )
        if verbose:
            print(f" score={judge_result.overall:.2f}")

        return AgentScenarioResult(
            scenario_name=scenario.name,
            adapter_name=adapter.name,
            agent_result=agent_result,
            judge_result=judge_result,
        )

    finally:
        adapter.teardown()


def run_agent_benchmark(
    adapters: list[MemoryAdapter],
    scenarios: list[AgentScenario],
    harness: AgentHarness,
    judge_model: str = "gpt-4o-mini",
    verbose: bool = False,
) -> list[AgentBenchmarkResult]:
    results = []

    for adapter in adapters:
        if verbose:
            print(f"\n{'=' * 60}")
            print(f"  {adapter.name}")
            print(f"{'=' * 60}")

        bench_result = AgentBenchmarkResult(adapter_name=adapter.name)

        for scenario in scenarios:
            if verbose:
                print(f"  {scenario.name}:")

            scenario_result = run_agent_scenario(
                adapter=adapter,
                scenario=scenario,
                harness=harness,
                judge_model=judge_model,
                verbose=verbose,
            )

            if verbose and scenario_result.skipped:
                print(f"    SKIP ({scenario_result.skip_reason})")

            bench_result.scenario_results[scenario.name] = scenario_result

        results.append(bench_result)

    return results
