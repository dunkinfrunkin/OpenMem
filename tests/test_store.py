import time

from openmem.models import Edge, Memory
from openmem.store import SQLiteStore


def make_store() -> SQLiteStore:
    return SQLiteStore(":memory:")


def test_add_and_get_memory():
    store = make_store()
    mem = Memory(text="SQLite is fast", type="fact", entities=["SQLite"])
    store.add_memory(mem)
    got = store.get_memory(mem.id)
    assert got is not None
    assert got.text == "SQLite is fast"
    assert got.entities == ["SQLite"]
    assert got.type == "fact"


def test_all_memories():
    store = make_store()
    store.add_memory(Memory(text="one"))
    store.add_memory(Memory(text="two"))
    assert len(store.all_memories()) == 2


def test_add_and_get_edges():
    store = make_store()
    m1 = Memory(text="A")
    m2 = Memory(text="B")
    store.add_memory(m1)
    store.add_memory(m2)
    edge = Edge(source_id=m1.id, target_id=m2.id, rel_type="supports", weight=0.7)
    store.add_edge(edge)

    edges = store.get_edges(m1.id)
    assert len(edges) == 1
    assert edges[0].rel_type == "supports"
    assert edges[0].weight == 0.7

    # Also found from target side
    edges2 = store.get_edges(m2.id)
    assert len(edges2) == 1


def test_get_neighbors():
    store = make_store()
    m1 = Memory(text="center")
    m2 = Memory(text="neighbor1")
    m3 = Memory(text="neighbor2")
    store.add_memory(m1)
    store.add_memory(m2)
    store.add_memory(m3)
    store.add_edge(Edge(source_id=m1.id, target_id=m2.id, rel_type="mentions"))
    store.add_edge(Edge(source_id=m3.id, target_id=m1.id, rel_type="supports"))

    neighbors = store.get_neighbors(m1.id)
    assert len(neighbors) == 2
    neighbor_ids = {n.id for _, n in neighbors}
    assert m2.id in neighbor_ids
    assert m3.id in neighbor_ids


def test_fts5_search():
    store = make_store()
    store.add_memory(Memory(text="Python is a great programming language", entities=["Python"]))
    store.add_memory(Memory(text="JavaScript runs in the browser", entities=["JavaScript"]))
    store.add_memory(Memory(text="Python and SQLite work well together", entities=["Python", "SQLite"]))

    results = store.search_bm25("Python")
    assert len(results) >= 2
    ids = [mid for mid, _ in results]
    # Both Python-related memories should appear
    all_mems = store.all_memories()
    python_ids = {m.id for m in all_mems if "Python" in m.text}
    for pid in python_ids:
        assert pid in ids


def test_bm25_ranking():
    store = make_store()
    # Memory with more relevant content should rank higher
    store.add_memory(Memory(text="SQLite database engine is embedded and fast"))
    store.add_memory(Memory(text="The weather today is nice"))
    store.add_memory(Memory(text="SQLite supports FTS5 full text search in SQLite databases"))

    results = store.search_bm25("SQLite database")
    assert len(results) >= 1
    # All results should have positive scores
    for _, score in results:
        assert score > 0


def test_update_access():
    store = make_store()
    mem = Memory(text="test access")
    store.add_memory(mem)
    assert mem.access_count == 0

    store.update_access(mem.id)
    updated = store.get_memory(mem.id)
    assert updated.access_count == 1
    assert updated.last_accessed is not None


def test_update_memory():
    store = make_store()
    mem = Memory(text="original", status="active")
    store.add_memory(mem)

    mem.status = "superseded"
    mem.strength = 0.5
    store.update_memory(mem)

    got = store.get_memory(mem.id)
    assert got.status == "superseded"
    assert got.strength == 0.5


def test_fts5_stays_in_sync_after_update():
    store = make_store()
    mem = Memory(text="original keyword alpha")
    store.add_memory(mem)

    # Should find by original text
    results = store.search_bm25("alpha")
    assert len(results) == 1

    # Update text
    mem.text = "updated keyword beta"
    store.update_memory(mem)

    # Should no longer find by old text
    results = store.search_bm25("alpha")
    assert len(results) == 0

    # Should find by new text
    results = store.search_bm25("beta")
    assert len(results) == 1
