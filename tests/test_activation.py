from openmem.activation import spread_activation
from openmem.models import Edge, Memory
from openmem.store import SQLiteStore


def make_graph():
    """Build a small test graph:
    A --0.8--> B --0.6--> C
    A --0.4--> D
    """
    store = SQLiteStore(":memory:")
    a = Memory(id="a", text="node A")
    b = Memory(id="b", text="node B")
    c = Memory(id="c", text="node C")
    d = Memory(id="d", text="node D")
    for m in [a, b, c, d]:
        store.add_memory(m)

    store.add_edge(Edge(source_id="a", target_id="b", weight=0.8))
    store.add_edge(Edge(source_id="b", target_id="c", weight=0.6))
    store.add_edge(Edge(source_id="a", target_id="d", weight=0.4))
    return store


def test_seed_only():
    store = make_graph()
    result = spread_activation({"a": 1.0}, store, max_hops=0)
    assert result == {"a": 1.0}


def test_one_hop():
    store = make_graph()
    result = spread_activation({"a": 1.0}, store, max_hops=1, decay_per_hop=0.5)
    assert "a" in result
    assert result["a"] == 1.0
    # B gets: 1.0 * 0.8 * 0.5^1 = 0.4
    assert abs(result["b"] - 0.4) < 1e-9
    # D gets: 1.0 * 0.4 * 0.5^1 = 0.2
    assert abs(result["d"] - 0.2) < 1e-9
    # C should NOT be reached in 1 hop
    assert result.get("c", 0) == 0


def test_two_hops():
    store = make_graph()
    result = spread_activation({"a": 1.0}, store, max_hops=2, decay_per_hop=0.5)
    # C gets: activation[b] * 0.6 * 0.5^2 = 0.4 * 0.6 * 0.25 = 0.06
    assert "c" in result
    assert abs(result["c"] - 0.06) < 1e-9


def test_no_self_downgrade():
    """Seeds should never have their activation lowered by spreading."""
    store = make_graph()
    result = spread_activation({"a": 1.0, "b": 0.9}, store, max_hops=1, decay_per_hop=0.5)
    # B was seeded at 0.9, spread from A would give 0.4, so B stays at 0.9
    assert result["b"] == 0.9


def test_empty_seeds():
    store = make_graph()
    result = spread_activation({}, store, max_hops=2)
    assert result == {}
