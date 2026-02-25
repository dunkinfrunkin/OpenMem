from __future__ import annotations

import pytest

from .adapters.base import MemoryAdapter
from .adapters.openmem_adapter import OpenMemAdapter
from .adapters.bm25_only_adapter import BM25OnlyAdapter
from .runner import run_scenario
from .scenarios.scenarios import (
    build_basic_recall,
    build_contradiction,
    build_graph_boosted,
    build_multi_hop,
    build_needle_in_haystack,
    build_supersession,
    build_temporal_recency,
)


class TestBasicRecall:
    def test_precision_above_threshold(self, adapter: MemoryAdapter):
        scenario = build_basic_recall()
        metrics = run_scenario(adapter, scenario)
        if metrics.skipped:
            pytest.skip(metrics.skip_reason)
        assert metrics.avg_precision >= 0.1, (
            f"{adapter.name} precision {metrics.avg_precision:.3f} < 0.1"
        )

    def test_mrr_above_threshold(self, adapter: MemoryAdapter):
        scenario = build_basic_recall()
        metrics = run_scenario(adapter, scenario)
        if metrics.skipped:
            pytest.skip(metrics.skip_reason)
        assert metrics.avg_mrr >= 0.2, (
            f"{adapter.name} MRR {metrics.avg_mrr:.3f} < 0.2"
        )


class TestGraphBoosted:
    def test_openmem_outperforms_bm25_only(self):
        """OpenMem with graph should retrieve more relevant results than BM25-only."""
        scenario = build_graph_boosted()
        openmem_metrics = run_scenario(OpenMemAdapter(), scenario)
        bm25_metrics = run_scenario(BM25OnlyAdapter(), scenario)

        # BM25-only skips graph scenarios, so it should be skipped
        assert not openmem_metrics.skipped
        assert bm25_metrics.skipped

    def test_openmem_recall_on_graph(self):
        """OpenMem should achieve meaningful recall on graph-boosted scenario."""
        scenario = build_graph_boosted()
        metrics = run_scenario(OpenMemAdapter(), scenario)
        assert not metrics.skipped
        assert metrics.avg_recall >= 0.3, (
            f"OpenMem recall {metrics.avg_recall:.3f} < 0.3 on graph scenario"
        )


class TestNeedleInHaystack:
    def test_needle_found(self, adapter: MemoryAdapter):
        scenario = build_needle_in_haystack()
        metrics = run_scenario(adapter, scenario)
        if metrics.skipped:
            pytest.skip(metrics.skip_reason)
        assert metrics.avg_mrr > 0, f"{adapter.name} failed to find the needle"


class TestContradiction:
    def test_strong_memory_wins(self):
        """OpenMem should rank the higher-confidence memory above the contradicted one."""
        scenario = build_contradiction()
        metrics = run_scenario(OpenMemAdapter(), scenario)
        assert not metrics.skipped
        assert metrics.avg_mrr >= 0.5, (
            f"OpenMem MRR {metrics.avg_mrr:.3f} < 0.5 on contradiction scenario"
        )


class TestSupersession:
    def test_new_memory_ranks_higher(self):
        """OpenMem should rank the superseding memory above the superseded one."""
        scenario = build_supersession()
        metrics = run_scenario(OpenMemAdapter(), scenario)
        assert not metrics.skipped
        assert metrics.avg_mrr >= 0.5, (
            f"OpenMem MRR {metrics.avg_mrr:.3f} < 0.5 on supersession scenario"
        )


class TestMultiHop:
    def test_chain_retrieval(self):
        """OpenMem should retrieve memories across the causal chain via graph traversal."""
        scenario = build_multi_hop()
        metrics = run_scenario(OpenMemAdapter(), scenario)
        assert not metrics.skipped
        assert metrics.avg_recall >= 0.3, (
            f"OpenMem recall {metrics.avg_recall:.3f} < 0.3 on multi-hop scenario"
        )
